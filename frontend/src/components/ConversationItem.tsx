import { ChatStore } from "../stroes/chatStore";
import { AuthStore } from "../stroes/authStroes";
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
  const me = AuthStore((s) => s.user);

  // Pick the other member as the display name
  const other = (conversation.members ?? []).find((m) => m.id !== me?.user_id);
  const displayName = other?.username ?? "Unknown";

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
