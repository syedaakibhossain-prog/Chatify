import { useState, useRef, useEffect } from "react";
import { usersApi } from "../api/users";
import { conversationApi } from "../api/conversations";
import { ChatStore } from "../stroes/chatStore";
import type { Conversation } from "../types";

export default function SearchUsers() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState<{ id: string; username: string } | null>(null);
  const [status, setStatus] = useState<"idle" | "loading" | "found" | "notfound" | "error">("idle");
  const [open, setOpen] = useState(false);
  const addConversation = ChatStore((s) => s.addConversation);
  const setActive = ChatStore((s) => s.setActiveConversation);
  const debounceRef = useRef<ReturnType<typeof setTimeout>>(undefined);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!query.trim()) {
      setOpen(false);
      setStatus("idle");
      return;
    }

    clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(async () => {
      setStatus("loading");
      setOpen(true);
      try {
        const user = await usersApi.search(query.trim());
        setResult(user);
        setStatus("found");
      } catch {
        setResult(null);
        setStatus("notfound");
      }
    }, 400);

    return () => clearTimeout(debounceRef.current);
  }, [query]);

  // Close on outside click
  useEffect(() => {
    function handler(e: MouseEvent) {
      if (containerRef.current && !containerRef.current.contains(e.target as Node)) {
        setOpen(false);
      }
    }
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  async function startChat(userId: string) {
    try {
      const raw = await conversationApi.create(userId);
      // raw is ConversationOut — adapt to Conversation shape for the store
      const conv: Conversation = {
        id: raw.id,
        created_at: raw.created_at,
        members: raw.members ?? [],
      };
      addConversation(conv);
      await setActive(conv.id);
    } catch {
      // conversation likely already exists; just search for it in the list
    }
    setQuery("");
    setOpen(false);
  }

  return (
    <div className="search-users" ref={containerRef}>
      <span className="search-icon">
        <svg width="15" height="15" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="2">
          <circle cx="9" cy="9" r="6" />
          <path d="M13.5 13.5 18 18" strokeLinecap="round" />
        </svg>
      </span>
      <input
        id="user-search-input"
        className="search-input"
        placeholder="Search users to start a chat…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onFocus={() => query.trim() && setOpen(true)}
        autoComplete="off"
      />

      {open && (
        <div className="search-dropdown">
          {status === "loading" && (
            <div className="search-no-result" style={{ display: "flex", alignItems: "center", gap: 8 }}>
              <div className="spinner" style={{ width: 14, height: 14 }} />
              Searching…
            </div>
          )}

          {status === "found" && result && (
            <div
              className="search-result-item"
              onClick={() => startChat(result.id)}
            >
              <div className="avatar-sm">{result.username.slice(0, 2).toUpperCase()}</div>
              <div>
                <div style={{ fontWeight: 600, fontSize: "0.875rem" }}>{result.username}</div>
                <div style={{ fontSize: "0.75rem", color: "var(--text-muted)" }}>Click to start chat</div>
              </div>
            </div>
          )}

          {status === "notfound" && (
            <div className="search-no-result">No user found for "{query}"</div>
          )}
        </div>
      )}
    </div>
  );
}
