import { ChatStore } from "../stroes/chatStore";
import type { Conversation } from "../types";

interface Props {
  conversation: Conversation;
  isActive: boolean;
}

function getInitials(name: string): string {
  return name.slice(0, 2).toUpperCase();
}

export default function ConversationItem({ conversation, isActive }: Props) {
  const setActive = ChatStore((s) => s.setActiveConversation);

  // Backend returns other_username directly — no members[] lookup needed
  const displayName = conversation.other_username ?? "Unknown";

  return (
    <div
      className={`conv-item${isActive ? " active" : ""}`}
      onClick={() => setActive(conversation.id)}
      role="button"
      tabIndex={0}
      onKeyDown={(e) => e.key === "Enter" && setActive(conversation.id)}
    >
      <div className="conv-avatar">{getInitials(displayName)}</div>
      <div className="conv-info">
        <div className="conv-name">{displayName}</div>
        <div className="conv-preview">Click to open chat</div>
      </div>
    </div>
  );
}
