import { create } from "zustand";
import { conversationApi } from "../api/conversations";
import { messagesApi } from "../api/messages";
import { chatSocket } from "../realtime/socket";
import type {
  Conversation,
  Message,
  WsInbound,
} from "../types";

interface TypingEntry {
  username: string;
  at: number;
}

interface ChatState {
  // ── Data ──────────────────────────────────────────────────────────
  conversations: Conversation[];
  /** Messages keyed by conversationId */
  messages: Record<string, Message[]>;
  activeConversationId: string | null;
  /** { conversationId: { userId: TypingEntry } } */
  typingUsers: Record<string, Record<string, TypingEntry>>;
  conversationsLoaded: boolean;

  // ── Actions ───────────────────────────────────────────────────────
  initSocket: () => void;
  teardown: () => void;
  loadConversations: () => Promise<void>;
  setActiveConversation: (id: string) => Promise<void>;
  loadMessages: (conversationId: string) => Promise<void>;
  sendMessage: (conversationId: string, content: string) => void;
  addConversation: (conv: Conversation) => void;
}

export const ChatStore = create<ChatState>((set, get) => {
  // Cleanup ref for WS subscription
  let _unsubscribe: (() => void) | null = null;

  // ── WebSocket frame handler ───────────────────────────────────────
  function handleWsFrame(msg: WsInbound): void {
    switch (msg.type) {
      case "message:new": {
        const { message } = msg;
        set((s) => {
          const prev = s.messages[message.conversation_id] ?? [];
          // avoid duplicates (might also come as ack)
          if (prev.find((m) => m.id === message.id)) return s;
          return {
            messages: {
              ...s.messages,
              [message.conversation_id]: [...prev, message],
            },
          };
        });
        break;
      }

      case "message:ack": {
        const { temp_id, message } = msg;
        set((s) => {
          const prev = s.messages[message.conversation_id] ?? [];
          const updated = prev
            .filter((m) => m.temp_id !== temp_id)          // remove optimistic
            .filter((m) => m.id !== message.id);            // avoid duplicates
          return {
            messages: {
              ...s.messages,
              [message.conversation_id]: [...updated, message],
            },
          };
        });
        break;
      }

      case "typing:update": {
        const { conversation_id, user_id, username, is_typing } = msg;
        set((s) => {
          const convTyping = { ...(s.typingUsers[conversation_id] ?? {}) };
          if (is_typing) {
            convTyping[user_id] = { username, at: Date.now() };
          } else {
            delete convTyping[user_id];
          }
          return {
            typingUsers: { ...s.typingUsers, [conversation_id]: convTyping },
          };
        });
        break;
      }

      case "read:update":
      case "ready":
      case "pong":
      case "error":
      default:
        break;
    }
  }

  return {
    conversations: [],
    messages: {},
    activeConversationId: null,
    typingUsers: {},
    conversationsLoaded: false,

    // ── initSocket ─────────────────────────────────────────────────
    initSocket: () => {
      chatSocket.connect();
      _unsubscribe = chatSocket.subscribe(handleWsFrame);
    },

    teardown: () => {
      _unsubscribe?.();
      chatSocket.disconnect();
      set({
        conversations: [],
        messages: {},
        activeConversationId: null,
        typingUsers: {},
        conversationsLoaded: false,
      });
    },

    // ── loadConversations ──────────────────────────────────────────
    loadConversations: async () => {
      try {
        // Step 1: get list of conversation IDs
        const ids = await conversationApi.list();
        if (!Array.isArray(ids) || ids.length === 0) {
          set({ conversations: [], conversationsLoaded: true });
          return;
        }

        // Step 2: fetch each conversation detail
        const settled = await Promise.allSettled(
          ids.map((id) => conversationApi.get(id))
        );

        const convs: Conversation[] = [];
        settled.forEach((r) => {
          if (r.status === "fulfilled" && r.value) convs.push(r.value);
        });

        set({ conversations: convs, conversationsLoaded: true });
      } catch {
        set({ conversationsLoaded: true });
      }
    },

    // ── setActiveConversation ──────────────────────────────────────
    setActiveConversation: async (id: string) => {
      set({ activeConversationId: id });
      chatSocket.sendMessageRead(id);

      // Load messages if not already cached
      if (!get().messages[id]) {
        await get().loadMessages(id);
      }
    },

    // ── loadMessages ───────────────────────────────────────────────
    loadMessages: async (conversationId: string) => {
      try {
        const res = await messagesApi.getMessages(conversationId);
        set((s) => ({
          messages: {
            ...s.messages,
            [conversationId]: res?.messages ?? [],
          },
        }));
      } catch {
        set((s) => ({
          messages: { ...s.messages, [conversationId]: [] },
        }));
      }
    },

    // ── sendMessage ────────────────────────────────────────────────
    sendMessage: (conversationId: string, content: string) => {
      const tempId = `tmp_${Date.now()}_${Math.random().toString(36).slice(2)}`;

      // Optimistic message
      const optimistic: Message = {
        id: tempId,
        conversation_id: conversationId,
        sender_id: "me",            // will be replaced by ack
        content,
        type: "text",
        created_st: new Date().toISOString(),
        is_deleted: false,
        pending: true,
        temp_id: tempId,
      };

      set((s) => ({
        messages: {
          ...s.messages,
          [conversationId]: [...(s.messages[conversationId] ?? []), optimistic],
        },
      }));

      chatSocket.sendMessage(conversationId, content, tempId);
    },

    // ── addConversation ────────────────────────────────────────────
    addConversation: (conv: Conversation) => {
      set((s) => {
        if (s.conversations.find((c) => c.id === conv.id)) return s;
        return { conversations: [conv, ...s.conversations] };
      });
    },
  };
});
