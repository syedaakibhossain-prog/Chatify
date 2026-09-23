import { useState, useRef, useCallback } from "react";
import { ChatStore } from "../stroes/chatStore";
import { chatSocket } from "../realtime/socket";

interface Props {
  conversationId: string;
}

const TYPING_DEBOUNCE_MS = 1500;

export default function MessageInput({ conversationId }: Props) {
  const [text, setText] = useState("");
  const sendMessage = ChatStore((s) => s.sendMessage);
  const isTypingRef = useRef(false);
  const typingTimerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  const stopTyping = useCallback(() => {
    if (isTypingRef.current) {
      isTypingRef.current = false;
      chatSocket.sendTypingStop(conversationId);
    }
  }, [conversationId]);

  function handleChange(e: React.ChangeEvent<HTMLTextAreaElement>) {
    setText(e.target.value);

    // Typing indicator
    if (!isTypingRef.current) {
      isTypingRef.current = true;
      chatSocket.sendTypingStart(conversationId);
    }
    clearTimeout(typingTimerRef.current);
    typingTimerRef.current = setTimeout(stopTyping, TYPING_DEBOUNCE_MS);
  }

  function handleSend() {
    const content = text.trim();
    if (!content) return;

    stopTyping();
    clearTimeout(typingTimerRef.current);

    sendMessage(conversationId, content);
    setText("");
  }

  function handleKeyDown(e: React.KeyboardEvent<HTMLTextAreaElement>) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  }

  return (
    <div className="message-input-area">
      <div className="message-input-row">
        <textarea
          id={`msg-input-${conversationId}`}
          className="message-textarea"
          rows={1}
          placeholder="Type a message… (Enter to send, Shift+Enter for newline)"
          value={text}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          autoFocus
        />
        <button
          id="send-message-btn"
          className="btn-send"
          onClick={handleSend}
          disabled={!text.trim()}
          aria-label="Send message"
        >
          {/* Paper-plane icon */}
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
            <line x1="22" y1="2" x2="11" y2="13" />
            <polygon points="22 2 15 22 11 13 2 9 22 2" />
          </svg>
        </button>
      </div>
    </div>
  );
}
