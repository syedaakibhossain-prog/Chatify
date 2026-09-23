import { useEffect } from "react";
import { AuthStore } from "../stroes/authStroes";
import { ChatStore } from "../stroes/chatStore";
import ConversationList from "../components/ConversationList";
import SearchUsers from "../components/SearchUsers";
import MessageList from "../components/MessageList";
import MessageInput from "../components/MessageInput";

export default function ChatPage() {
  const user = AuthStore((s) => s.user);
  const logout = AuthStore((s) => s.logout);

  const initSocket = ChatStore((s) => s.initSocket);
  const teardown = ChatStore((s) => s.teardown);
  const conversations = ChatStore((s) => s.conversations);
  const activeId = ChatStore((s) => s.activeConversationId);

  // Connect WS when chat page mounts, disconnect on unmount
  useEffect(() => {
    initSocket();
    return () => teardown();
  }, [initSocket, teardown]);

  // Find the active conversation to show the header name
  const activeConversation = conversations.find((c) => c.id === activeId);
  const other = activeConversation?.members?.find((m) => m.id !== user?.user_id);
  const chatPartnerName = other?.username ?? "Chat";

  function getInitials(name: string) {
    return name.slice(0, 2).toUpperCase();
  }

  return (
    <div className="chat-layout">
      {/* ── Sidebar ── */}
      <aside className="sidebar">
        {/* Logo + User */}
        <header className="sidebar-header">
          <span className="sidebar-logo">Chatify</span>
          <div className="sidebar-user">
            <div className="sidebar-avatar">
              {user?.username?.slice(0, 2).toUpperCase() ?? "??"}
            </div>
            <span className="sidebar-username">{user?.username}</span>
            <button
              id="logout-btn"
              className="btn-logout"
              onClick={logout}
              title="Log out"
            >
              ↪
            </button>
          </div>
        </header>

        {/* User Search */}
        <SearchUsers />

        {/* Conversation List */}
        <ConversationList />
      </aside>

      {/* ── Chat Main ── */}
      <main className="chat-main">
        {activeId ? (
          <>
            {/* Chat header */}
            <div className="chat-header">
              <div className="chat-header-avatar">
                {getInitials(chatPartnerName)}
              </div>
              <div>
                <div className="chat-header-name">{chatPartnerName}</div>
                <div className="chat-header-status">Online</div>
              </div>
            </div>

            {/* Messages */}
            <MessageList conversationId={activeId} />

            {/* Input */}
            <MessageInput conversationId={activeId} />
          </>
        ) : (
          <div className="chat-empty">
            <div className="chat-empty-icon">💬</div>
            <div className="chat-empty-title">Welcome to Chatify</div>
            <div className="chat-empty-sub">
              Select a conversation from the sidebar, or search for a user to start chatting.
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
