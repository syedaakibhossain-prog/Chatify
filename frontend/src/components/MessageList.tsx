import { useEffect, useRef } from "react";
import { ChatStore } from "../stroes/chatStore";
import { AuthStore } from "../stroes/authStroes";
import MessageBubble from "./MessageBubble";
import TypingIndicator from "./TypingIndicator";

interface Props {
  conversationId: string;
}

export default function MessageList({ conversationId }: Props) {
  const messages = ChatStore((s) => s.messages[conversationId]) ?? [];
  const typingMap = ChatStore((s) => s.typingUsers[conversationId]) ?? {};
  const me = AuthStore((s) => s.user);
  const bottomRef = useRef<HTMLDivElement>(null);

  // Scroll to bottom on new messages
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  // Names of people currently typing (exclude self)
  const typingNames = Object.entries(typingMap)
    .filter(([userId]) => userId !== me?.user_id)
    .map(([, entry]) => entry.username);

  if (messages.length === 0) {
    return (
      <div className="message-list" style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ color: "var(--text-muted)", fontSize: "0.875rem" }}>
          No messages yet — say hello! 👋
        </div>
      </div>
    );
  }

  return (
    <>
      <div className="message-list">
        {messages.map((msg) => (
          <MessageBubble
            key={msg.temp_id ?? msg.id}
            message={msg}
            isMine={msg.sender_id === me?.user_id || msg.sender_id === "me"}
          />
        ))}
        <div ref={bottomRef} />
      </div>
      <TypingIndicator names={typingNames} />
    </>
  );
}
