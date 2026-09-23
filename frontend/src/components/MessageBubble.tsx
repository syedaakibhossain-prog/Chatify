import type { Message } from "../types";

interface Props {
  message: Message;
  isMine: boolean;
}

function formatTime(isoStr: string): string {
  try {
    return new Date(isoStr).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return "";
  }
}

export default function MessageBubble({ message, isMine }: Props) {
  const rowClass = `bubble-row ${isMine ? "own" : "other"}`;

  let bubbleClass = `bubble ${isMine ? "own" : "other"}`;
  if (message.pending) bubbleClass += " pending";
  if (message.failed) bubbleClass += " failed";

  // Support both created_at and created_st (typo in backend type)
  const timestamp =
    (message as unknown as { created_at?: string }).created_at ??
    message.created_st;

  return (
    <div className={rowClass}>
      <div className={bubbleClass}>
        {message.is_deleted ? (
          <em style={{ opacity: 0.6 }}>Message deleted</em>
        ) : (
          message.content
        )}
        <span className="bubble-time">
          {message.pending
            ? "Sending…"
            : message.failed
            ? "Failed"
            : formatTime(timestamp)}
        </span>
      </div>
    </div>
  );
}
