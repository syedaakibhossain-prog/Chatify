# Chatify — Frontend Development Guide

This document is derived from a read-through of the `backend/` folder (FastAPI + SQLAlchemy + SQLite, cookie-based JWT auth, WebSocket chat). It gives a frontend developer everything needed to build the client: base setup, REST endpoints, request/response shapes, the WebSocket protocol, and known backend quirks to design around.

---

## 1. Stack & Base Setup

- **Backend**: FastAPI, async SQLAlchemy, SQLite (`database.db`)
- **Auth**: JWT access + refresh tokens, delivered as **httpOnly cookies** (not returned in the JSON body)
- **Base URL**: `http://localhost:8000` (default uvicorn port; confirm with whoever runs the backend)
- **Content type**: `application/json` for all REST calls
- **Credentials**: every `fetch`/`axios` call must include cookies, e.g.
  ```js
  fetch(url, { credentials: "include", ... })
  // or with axios
  axios.defaults.withCredentials = true;
  ```

### ⚠️ CORS configuration issue to flag to your backend dev
`main.py` currently sets:
```python
allow_origins="http://127.0.0.1:5500/test/test.html"
```
This is a **string**, not a list, and it's a very specific path — not an origin. FastAPI's CORS middleware expects a list of *origins* (scheme + host + port only, e.g. `"http://localhost:3000"`). As written, requests from a real frontend dev server (e.g. Vite on `http://localhost:5173`, CRA on `:3000`) will likely be **blocked**, and cookies won't be set cross-origin. Ask the backend owner to change this to something like:
```python
allow_origins=["http://localhost:3000"],  # your frontend dev URL
allow_credentials=True,
```
(The `config.py` file already has an unused `ALLOWED_ORIGINS` setting meant for this.)

---

## 2. Authentication

All auth endpoints are under `/auth`.

| Method | Path | Auth required | Purpose |
|---|---|---|---|
| POST | `/auth/register` | No | Create a new user |
| POST | `/auth/login` | No | Log in, sets cookies |
| POST | `/auth/refresh` | Refresh cookie | Rotate access token |
| POST | `/auth/logout` | No | Clears cookies |
| GET | `/auth/me` | Access cookie | Get current user |

### Register
`POST /auth/register`
```json
// Request
{
  "username": "alice",     // 3–20 chars
  "email": "alice@example.com",
  "password": "somepassword123"  // 8–70 chars
}
```
```json
// 201 Response
{
  "user_id": "uuid",
  "username": "alice",
  "email": "alice@example.com"
}
```
Errors: `409` if username or email already exists.

### Login
`POST /auth/login`
```json
// Request
{ "email": "alice@example.com", "password": "somepassword123" }
```
On success (`200`), the server sets two cookies automatically (nothing to store in JS):
- `access_token` — httpOnly, 1 hour (`max_age=3600`)
- `refresh_token` — httpOnly, 30 days

Response body:
```json
{ "user_id": "uuid", "username": "alice", "email": "alice@example.com" }
```
Errors: `401` invalid credentials.

**Frontend implication:** because tokens are httpOnly cookies, you **cannot read the JWT from JS**, and you don't need to (no `Authorization` header handling). Just make sure `credentials: "include"` is set and the frontend's dev server origin matches CORS config.

### Refresh
`POST /auth/refresh` — no body needed, browser sends the `refresh_token` cookie automatically. Returns a new `access_token` cookie + the user object. Call this when you get a `401` on a protected route, then retry the original request once.

### Logout
`POST /auth/logout` → `204 No Content`, clears both cookies.

### Get current user
`GET /auth/me` → returns the logged-in user; use this on app load to check session state (e.g. in an `AuthContext`/root loader). `401` means "not logged in" — route to the login page.

### Suggested frontend auth flow
1. On app load, call `GET /auth/me`.
   - Success → store user in global state, render app.
   - `401` → try `POST /auth/refresh` once; if that also fails, show the login screen.
2. Wrap all API calls in a helper that retries once with `/auth/refresh` on a `401`.
3. Login/Register forms just call the endpoints above and then re-fetch `/auth/me` (or use the response body directly).

---

## 3. Conversations

Base path: `/conversations`. All routes require auth (cookie).

| Method | Path | Purpose |
|---|---|---|
| POST | `/conversations` | Create a conversation |
| GET | `/conversations/{conversation_id}` | Get a conversation by id |

### Create conversation
`POST /conversations`
```json
// Request — IDs of the OTHER user(s) you're chatting with
{ "user_ids": ["other-user-uuid"] }
```
The backend automatically adds the current (authenticated) user to the member list, and requires **at least 2 total members** — so for a 1:1 chat, send just the other person's `user_ids` and the server adds you.

```json
// 201 Response
{ "id": "conversation-uuid" }
```
Note: the response only contains the conversation `id` — no member list or metadata is returned yet. If you need to show participant names/avatars in a chat list UI, you'll likely need to track this locally when you create the conversation, or ask the backend to extend `ConversationResponse` with a members array.

### Get conversation
`GET /conversations/{conversation_id}` → `{ "id": "uuid" }` (same minimal shape). `404` if it doesn't exist, `403` if the current user isn't a member.

There is currently **no "list my conversations" endpoint** — you'll need one to build a conversation/sidebar list. Flag this to the backend team, or track conversation IDs client-side as they're created.

---

## 4. Messages

Base path: `/messages`. All routes require auth (cookie).

| Method | Path | Purpose |
|---|---|---|
| POST | `/messages/conversations/{conversession_id}` | Send a message (REST) |
| GET | `/messages/conversations/{conversession_id}` | Fetch message history |
| PATCH | `/messages/{message_id}` | Edit a message |
| DELETE | `/messages/{message_id}` | Soft-delete a message |

> Note the backend's own spelling: **`conversession`**, not "conversation" — this typo is baked into route paths, field names, and JSON keys throughout. Copy it exactly.

### Send message
`POST /messages/conversations/{conversession_id}`
```json
// Request
{ "content": "hey there!" }  // 1–1000 chars
```
```json
// 201 Response
{
  "id": "uuid",
  "conversession_id": "uuid",
  "sender_id": "uuid",
  "content": "hey there!",
  "created_at": "2026-09-10T12:00:00",
  "is_deleted": false,
  "deleted_at": null
}
```
In practice you'll mostly send messages over the **WebSocket** (below) for real-time delivery; this REST endpoint is useful as a fallback or for non-realtime clients.

### Get message history
`GET /messages/conversations/{conversession_id}` → `MessageResponse[]`, newest-first (`ORDER BY created_at DESC`), limited to 50 by default (no pagination params are exposed yet — hard-coded `limit=50` server-side). Deleted messages are excluded automatically.

**Frontend implication:** reverse the array (or use `flex-direction: column-reverse`) to render oldest-to-newest in a chat window. There's no `before`/`cursor` param for infinite scroll yet — worth requesting from backend if you need "load older messages."

### Edit message
`PATCH /messages/{message_id}`
```json
{ "content": "edited text" }
```
Returns the updated `MessageResponse`. `403` if you're not the sender, `400` if already deleted.

⚠️ This REST edit **does not broadcast over the WebSocket** — other connected clients won't see the edit live unless you also refetch or the backend is extended to push a `message_updated` WS event. Plan your UI accordingly (e.g. re-fetch that conversation's messages after a successful edit).

### Delete message
`DELETE /messages/{message_id}` — soft delete (`is_deleted = true`), returns the updated `MessageResponse`. Same caveat: **no WebSocket broadcast** for deletes either. `403` if not the sender, `400` if already deleted.

---

## 5. Real-time Chat (WebSocket)

### Connecting
```
ws://localhost:8000/ws/conversession/{conversession_id}?user_id={user_id}
```
- `conversession_id` is a path parameter (the conversation UUID).
- `user_id` is passed as a **query parameter** (not read from the auth cookie!).

⚠️ **Known backend issue:** the WebSocket auth check (`WebAuth.authenticate_user`) currently only verifies that the given `user_id` **exists as a user** — it does not verify a JWT or session at all. Anyone who knows another user's UUID could open a socket "as" them. There's also a `WebAuth(user_repo)` construction bug in `routes.py` (the class expects `db` and `user_repo`, but is only given one argument) — this will raise at import/startup time until fixed. **Flag both to your backend developer**; don't rely on the WS connection being secure until it validates the real access-token cookie the same way REST routes do.

For frontend planning purposes, build your socket client as if it will eventually authenticate via the same cookie/session as REST calls (i.e. don't hardcode a design that requires passing `user_id` in the URL — treat it as temporary).

### Message format — client → server
```json
{ "type": "message", "content": "hello!" }
```
Only `"type": "message"` is currently supported; any other type raises an error that's echoed back.

### Message format — server → client (broadcast to all members of the room)
```json
{
  "type": "message",
  "data": {
    "id": "uuid",
    "conversession_id": "uuid",
    "sender_id": "uuid",
    "content": "hello!",
    "created_at": "2026-09-10T12:00:00"
  }
}
```

### Error format — server → client
```json
{ "type": "error", "detail": "explanation string" }
```
Sent for invalid JSON or any exception while handling a message (e.g. sending to a conversation you're not a member of).

### Suggested client-side socket flow
1. After loading a conversation's REST history (`GET /messages/conversations/{id}`), open a WebSocket to `/ws/conversession/{id}?user_id={me}`.
2. On `onmessage`, parse JSON:
   - `type === "message"` → append `data` to the message list (dedupe against optimistic local messages by matching `content` + a temporary flag, or wait for server echo before rendering).
   - `type === "error"` → show a toast / log; the socket is *not* closed by the server in this case, so no need to reconnect.
3. On send, you can either:
   - Send over the WebSocket only (`{"type": "message", "content": "..."}`) — the server persists it and broadcasts to all members, including you.
   - Or POST via REST and rely on the WS broadcast (the server persists in `handel_message` too, so don't do both for the same message).
4. On `onclose`, attempt reconnect with backoff, and re-fetch recent history on reconnect in case any broadcasts were missed while disconnected.
5. One WebSocket connection per open conversation (the server keys rooms by `conversession_id`).

---

## 6. Data Models Reference

### User
| Field | Type | Notes |
|---|---|---|
| id | UUID | |
| username | string | unique, 3–20 chars |
| email | string | unique |
| last_seen | datetime | set server-side, not currently updated on activity |

### Conversation (`Conversession`)
| Field | Type |
|---|---|
| id | UUID |

(Members are modeled via a separate `Member` join table — not exposed via API response shapes yet, only used internally for membership checks.)

### Message
| Field | Type | Notes |
|---|---|---|
| id | UUID | |
| conversession_id | UUID | |
| sender_id | UUID | |
| content | string | max 1000 chars |
| created_at | datetime | |
| is_deleted | bool | soft-delete flag |
| deleted_at | datetime \| null | |

---

## 7. Error Handling Conventions

REST errors follow FastAPI's default shape:
```json
{ "detail": "human-readable message" }
```
Common status codes you'll handle in the UI:
- `401` — not authenticated / expired token → trigger refresh flow or redirect to login
- `403` — authenticated but not a member of the conversation / not the message owner
- `404` — conversation or message not found
- `409` — username/email already taken (registration)
- `400` — validation error (e.g. editing/deleting an already-deleted message, fewer than 2 members)

---

## 8. Suggested Frontend Architecture

A reasonable structure for a React (or similar SPA) client:

```
src/
  api/
    client.js          # fetch wrapper: credentials:"include", 401→refresh retry
    auth.js             # register, login, logout, me, refresh
    conversations.js    # createConversation, getConversation
    messages.js         # getMessages, sendMessage, editMessage, deleteMessage
    socket.js           # WebSocket connect/reconnect + event dispatch
  context/
    AuthContext.jsx      # current user, login/logout actions
    ChatContext.jsx       # active conversation, message list, socket lifecycle
  pages/
    LoginPage.jsx
    RegisterPage.jsx
    ChatPage.jsx           # sidebar (if you build a conversation-list feature) + message thread
  components/
    MessageList.jsx
    MessageInput.jsx
    MessageBubble.jsx      # handle is_deleted / edited states
    ConversationList.jsx   # requires a "list my conversations" endpoint — see gap below
```

### Gaps to close with the backend team before/while building the UI
1. **List conversations for a user** — no endpoint exists; needed for any sidebar/inbox UI.
2. **Conversation metadata** (member usernames, last message preview) — current response is just `{id}`.
3. **Fix CORS `allow_origins`** to a real list of frontend origins.
4. **WebSocket auth** — currently trusts a client-supplied `user_id`; also has a startup-breaking constructor bug (`WebAuth(user_repo)` vs. `WebAuth(db, user_repo)`).
5. **Live broadcast for edit/delete** — currently REST-only, so other clients won't see edits/deletes in real time without a refetch or polling.
6. **Pagination** for message history (`limit` is fixed at 50, no cursor).

None of these block you from starting the UI — just design with graceful fallbacks (e.g., poll or refetch periodically, track known conversation IDs in local storage) until the backend adds them.
