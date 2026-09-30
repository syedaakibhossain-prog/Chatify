import { useEffect, useState } from "react";
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
  const setActiveConversation = ChatStore((s) => s.setActiveConversation);

  // Mobile: true = show sidebar, false = show chat panel
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(true);

  // Connect WS when chat page mounts, disconnect on unmount
  useEffect(() => {
    initSocket();
    return () => teardown();
  }, [initSocket, teardown]);

  // When a conversation becomes active on mobile, switch to chat view
  useEffect(() => {
    if (activeId) setMobileSidebarOpen(false);
  }, [activeId]);

  // Find the active conversation to show the header name
  const activeConversation = conversations.find((c) => c.id === activeId);
  const chatPartnerName = activeConversation?.other_username ?? "Chat";

  function getInitials(name: string) {
    return name.slice(0, 2).toUpperCase();
  }

  function handleBackToSidebar() {
    setMobileSidebarOpen(true);
    setActiveConversation(null);
  }

  return (
    <div className="chat-layout">
      {/* ── Sidebar ── */}
      <aside className={`sidebar${mobileSidebarOpen ? " mobile-visible" : " mobile-hidden"}`}>
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
      <main className={`chat-main${!mobileSidebarOpen ? " mobile-visible" : " mobile-hidden"}`}>
        {activeId ? (
          <>
            {/* Chat header */}
            <div className="chat-header">
              {/* Back button — only visible on mobile */}
              <button
                id="back-to-sidebar-btn"
                className="btn-back-mobile"
                onClick={handleBackToSidebar}
                aria-label="Back to conversations"
              >
                ←
              </button>
              <div className="chat-header-avatar">
                {getInitials(chatPartnerName)}
              </div>
              <div>
                <div className="chat-header-name">{chatPartnerName}</div>
                <div className="chat-header-status">
                  <span className="status-dot" />
                  Online
                </div>
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
