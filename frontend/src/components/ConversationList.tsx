import { useEffect } from "react";
import { ChatStore } from "../stroes/chatStore";
import ConversationItem from "./ConversationItem";

export default function ConversationList() {
  const conversations = ChatStore((s) => s.conversations);
  const activeId = ChatStore((s) => s.activeConversationId);
  const loadConversations = ChatStore((s) => s.loadConversations);
  const loaded = ChatStore((s) => s.conversationsLoaded);

  useEffect(() => {
    loadConversations();
  }, [loadConversations]);

  if (!loaded) {
    return (
      <div className="conversation-list">
        <div className="conversation-list-empty">
          <div className="spinner" />
          <span>Loading chats…</span>
        </div>
      </div>
    );
  }

  if (conversations.length === 0) {
    return (
      <div className="conversation-list">
        <div className="conversation-list-empty">
          <span style={{ fontSize: "1.8rem" }}>💬</span>
          <span>No conversations yet</span>
          <span style={{ fontSize: "0.78rem" }}>
            Search for a user above to start chatting
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="conversation-list">
      {conversations.map((conv) => (
        <ConversationItem
          key={conv.id}
          conversation={conv}
          isActive={conv.id === activeId}
        />
      ))}
    </div>
  );
}
