# Chatify — Frontend Design Document (React, minimal UI)

Companion to `chatify-frontend-guide.md`. That document covers the API; this one covers **what to build and how it should look**.

Design goal: a calm, minimal messaging UI. Two panes, one accent color, no visual noise. Think "quiet utility," not "flashy chat app."

---

## 1. Design principles

1. **One accent color, used sparingly** — only for your own outgoing messages and primary actions (send button). Everything else is neutral gray/white.
2. **Flat surfaces, no shadows or gradients.** Structure comes from thin borders (1px, low-contrast) and whitespace, not depth effects.
3. **Generous whitespace over dense chrome.** No sidebars-within-sidebars, no toolbars. If a feature isn't in the API guide's MVP scope (§8 of that doc), don't build a UI for it yet.
4. **Sentence case everywhere.** No Title Case, no ALL CAPS, no exclamation marks in system copy.
5. **Type does the work.** One font, two weights (400 regular, 500 medium). No decorative headings.

---

## 2. Visual language

### Color tokens
| Token | Hex (light) | Usage |
|---|---|---|
| `--bg-page` | `#FAFAF9` | App background |
| `--bg-surface` | `#FFFFFF` | Sidebar, message thread panel |
| `--bg-bubble-in` | `#F1F1EF` | Incoming message bubble |
| `--bg-bubble-out` | `#DCEBFB` | Outgoing message bubble (accent tint) |
| `--text-primary` | `#1A1A18` | Main text |
| `--text-secondary` | `#6B6A66` | Timestamps, muted labels |
| `--border` | `#E5E4E0` | Hairline dividers |
| `--accent` | `#2F6FE0` | Send button, active conversation, links |
| `--danger` | `#C23B34` | Delete confirmation, error text |

Dark mode: invert to `#171715` page / `#1F1F1D` surface / `#2A2A27` incoming bubble / `#1E3A5F` outgoing bubble tint, same accent blue, text flipped to near-white/gray. Build with CSS variables from day one so dark mode is a token swap, not a rewrite.

### Typography
- Font: system UI stack (`-apple-system, "Segoe UI", Inter, sans-serif`) — no custom webfont needed for a minimal UI.
- Sizes: 13px (timestamps/meta), 14px (body/messages), 15px (usernames, section titles), 18px (page/app title). Two weights only: 400 and 500.
- Line height 1.5 for message text.

### Spacing & shape
- Base spacing unit: 8px (use 8/12/16/24 throughout).
- Corner radius: 8px for buttons/inputs, 12px for message bubbles and cards.
- Borders: 1px solid `--border`, never shadows.

---

## 3. Screens

### 3.1 Login
Centered card, max-width 360px, vertically centered on the page.
- App name (18px/500)
- Email input
- Password input
- "Log in" button (accent fill, full width)
- Text link below: "Don't have an account? Create one"
- Inline error text (13px, `--danger`) above the button on failed login — no toast/modal.

### 3.2 Register
Same layout as login: username, email, password, password requirements as muted helper text under the field (not a popover). "Create account" button. Link back to login.

### 3.3 Main chat screen (two-pane layout)
This is the app's only real screen once logged in.

```
┌───────────────┬─────────────────────────────────────┐
│ Chatify        │  Maya Rodriguez                      │  ← header, 56px
├───────────────┼─────────────────────────────────────┤
│ Maya Rodriguez │                                       │
│ Design team    │      [incoming bubble]                │
│ Sam Ortiz      │                    [outgoing bubble]  │  ← scrollable thread
│                │      [incoming bubble]                │
│                │                                       │
├───────────────┼─────────────────────────────────────┤
│                │  [ message input........ ] [send →]  │  ← composer, 56px
└───────────────┴─────────────────────────────────────┘
   240px fixed          flex: 1
```

**Left pane — conversation list**
- App name/logo at top, 56px header, border-bottom.
- List of conversations, each row: name, 14px, with the active one highlighted via a light gray background fill (`--fill-ghost-selected` equivalent) — not a colored bar or badge.
- No avatars in v1 (keeps it minimal); add later only if needed.
- No unread badges, no last-message preview in v1 — the API doesn't return this yet (see gaps in the API doc). Keep the row simple until that's available.

**Right pane — message thread**
- Header: other participant's name only, 15px/500, border-bottom.
- Message list: bubbles left-aligned (incoming, gray) or right-aligned (outgoing, accent tint), max-width ~60% of pane, 12px radius, 8×12px padding, 8px gap between bubbles.
- Timestamp: 12px `--text-secondary`, shown on hover only (not permanently visible) to reduce clutter — or, simpler for v1, shown once per cluster of consecutive messages from the same sender.
- Deleted messages: render as a single muted line — "message deleted" in italic `--text-secondary`, no bubble background.
- Composer: single-line text input that grows up to ~4 lines, plain "send" button (accent fill, arrow icon) to the right. Enter sends, Shift+Enter adds a newline.

### 3.4 Empty / edge states
- **No conversation selected:** center pane shows muted text "Select a conversation to start chatting." No illustration — keep it plain.
- **No conversations yet:** left pane shows "No conversations yet" in muted text.
- **Connecting / reconnecting socket:** small muted text under the header, e.g. "Reconnecting…" — no modal, no spinner overlay.

---

## 4. Components (React, plain JS — no UI kit needed)

```
src/
  components/
    AuthForm.jsx           # shared shell for Login/Register (fields + submit)
    ConversationList.jsx   # left pane list
    ConversationRow.jsx    # single row, active state
    ChatHeader.jsx         # right pane top bar
    MessageThread.jsx      # scrollable list, auto-scrolls to bottom on new message
    MessageBubble.jsx      # incoming/outgoing/deleted variants
    MessageComposer.jsx    # textarea + send button, Enter/Shift+Enter handling
  pages/
    LoginPage.jsx
    RegisterPage.jsx
    ChatPage.jsx            # renders ConversationList + (ChatHeader/MessageThread/MessageComposer or empty state)
```

Keep components presentational where possible; put fetch/socket logic in the `api/` and `context/` layers described in the API guide (§8).

### Component states worth designing for explicitly
- `MessageBubble`: `pending` (optimistic, sent but not yet confirmed by server — render at ~70% opacity), `sent`, `deleted`.
- `MessageComposer`: disabled/empty send button when the input is blank; no other validation needed given the API's 1–1000 char limit (just truncate or show a small counter near the limit, e.g. only past 900 chars).
- `ConversationRow`: default, active (selected), nothing else — no unread state until the API supports it.

---

## 5. Interaction & motion

Minimal by default — most "interactions" should just be instant state changes, not animated ones:
- New message appended → thread auto-scrolls to bottom (smooth scroll, ~150ms).
- Sending a message → bubble appears immediately (optimistic), fades from 70%→100% opacity when the server confirms (~150ms), no spinner.
- Switching conversations → no transition, just swap content (avoids feeling sluggish).
- Avoid modals wherever possible. Confirming a delete: use inline "delete this message?" with confirm/cancel text buttons in place of the bubble content, not a popup dialog.

---

## 6. Responsive behavior

- **Desktop (≥768px):** two-pane layout as above, sidebar fixed at 240px.
- **Mobile (<768px):** single-pane, stack navigation — conversation list is the default view; tapping a conversation pushes the thread view full-screen with a back arrow in the header. No need for a persistent sidebar on small screens.

---

## 7. Accessibility notes
- All interactive elements (rows, buttons) reachable by keyboard, with a visible focus ring (2px accent outline).
- Message input has an associated `aria-label="Message"`.
- Deleted-message text and timestamps should still meet 4.5:1 contrast against their background even though they're "muted."

---

## 8. What this design deliberately leaves out (v1 scope)

To keep the UI minimal and match the current backend's real capabilities (see gaps listed in the API guide), v1 does **not** include:
- Avatars / profile photos
- Unread counts or last-message previews in the sidebar
- Typing indicators or online/offline status
- Message reactions
- File/image attachments
- Group conversation naming or member management UI (backend supports multi-member conversations, but there's no endpoint yet to name a group or list its members)

Add these later as the backend grows; the component structure above (especially `ConversationRow` and `MessageBubble`) is built so each can be extended with a new prop rather than a redesign.
