# Chatify

A real-time chat application built with a FastAPI backend and a React frontend. Messages are delivered instantly over WebSockets, with optimistic UI updates and live typing indicators.

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Backend Setup](#backend-setup)
  - [Frontend Setup](#frontend-setup)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [WebSocket Protocol](#websocket-protocol)
- [Rate Limiting](#rate-limiting)
- [Database Models](#database-models)

---

## Overview

Chatify is a one-on-one messaging application. Users can register, search for other users, start conversations, and exchange messages in real time. The backend exposes a REST API for data operations and a WebSocket endpoint for live event delivery. The frontend is a single-page application that maintains a persistent WebSocket connection while the user is logged in.

---

## Features

- User registration and login with JWT authentication (access and refresh tokens stored as HTTP-only cookies)
- Token refresh without re-login
- Search for other users by username
- Create and list one-on-one conversations
- Real-time message delivery via WebSocket
- Optimistic message rendering on the sender side
- Live typing indicators (`typing:start` / `typing:stop`)
- Read receipts (`message:read` / `read:update`)
- Redis-backed rate limiting on all HTTP endpoints
- Persistent message history loaded on demand

---

## Architecture

```
Browser  <──REST──>  FastAPI  <──SQLAlchemy──>  SQLite (dev)
         <──WS────>  (uvicorn)
                         |
                       Redis  (rate limiting, WebSocket state)
```

- The backend is a single async FastAPI process. All database calls use `aiosqlite` through SQLAlchemy's async engine, so no threads are blocked.
- The WebSocket manager keeps an in-memory mapping of `user_id -> [WebSocket]` and `conversation_id -> {user_id}`, enabling fan-out to all members of a conversation.
- Redis is used exclusively for rate limiting in the current implementation. The server refuses to start if Redis is unavailable.
- The frontend connects to the WebSocket endpoint once the user is authenticated and keeps the connection alive with `ping` / `pong` frames.

---

## Tech Stack

### Backend

| Layer | Technology |
|---|---|
| Framework | FastAPI |
| ASGI server | Uvicorn |
| ORM | SQLAlchemy 2 (async) |
| Database (dev) | SQLite via `aiosqlite` |
| Auth | JWT (`HS256`) with HTTP-only cookies |
| Caching / Rate limiting | Redis (`redis-py` async) |
| Settings | `pydantic-settings` |

### Frontend

| Layer | Technology |
|---|---|
| Framework | React 19 |
| Language | TypeScript |
| Bundler | Vite |
| Routing | React Router v7 |
| State management | Zustand |
| Styling | Tailwind CSS v3 |

---

## Project Structure

```
chatify/
├── backend/
│   └── src/
│       ├── main.py               # FastAPI app, lifespan, CORS, router registration
│       ├── config.py             # Settings loaded from .env via pydantic-settings
│       ├── database.py           # SQLAlchemy async engine and session factory
│       ├── model.py              # ORM models: User, Conversation, Member, Message
│       ├── dependences.py        # Shared FastAPI dependencies (get_user, etc.)
│       ├── utils.py              # Shared utility helpers
│       ├── authentication/       # Register, login, refresh, logout, /me
│       ├── user/                 # User search and profile endpoints
│       ├── converseation/        # Conversation CRUD
│       ├── message/              # Message history and send (REST fallback)
│       ├── realtime/             # WebSocket endpoint, connection manager, event handler
│       └── redis/                # Redis client, rate limiter, rate limit configs
└── frontend/
    └── src/
        ├── App.tsx               # Route definitions and auth guard
        ├── pages/
        │   ├── loginPage.tsx
        │   ├── registerPage.tsx
        │   └── chatPage.tsx
        ├── components/
        │   ├── ConversationList.tsx
        │   ├── ConversationItem.tsx
        │   ├── MessageList.tsx
        │   ├── MessageBubble.tsx
        │   ├── MessageInput.tsx
        │   ├── SearchUsers.tsx
        │   └── TypingIndicator.tsx
        ├── api/                  # Fetch wrappers for each REST resource
        ├── realtime/
        │   └── socket.ts         # WebSocket client with reconnect logic
        ├── stroes/
        │   ├── authStroes.ts     # Auth state (bootstrap, login, logout)
        │   └── chatStore.ts      # Conversations, messages, typing, WS frame handler
        └── types/                # Shared TypeScript types
```

---

## Getting Started

### Prerequisites

- Python 3.11 or later
- Node.js 20 or later
- A running Redis instance (default: `redis://localhost:6379/0`)

### Backend Setup

```bash
# 1. Create and activate a virtual environment
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. Copy the example env file and adjust values
copy src\.env.example src\.env    # Windows
# cp src/.env.example src/.env   # macOS / Linux

# 4. Start the development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`. Interactive docs are at `http://localhost:8000/docs`.

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app will be available at `http://localhost:5173`.

---

## Environment Variables

Create `backend/src/.env` with the following keys:

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | `sqlite+aiosqlite:///./database.db` | SQLAlchemy async database URL |
| `JWT_ACCESS_SECRET_KEY` | — | Secret used to sign access tokens |
| `JWT_REFRESH_SECRET_KEY` | — | Secret used to sign refresh tokens |
| `ENCRYPTION_ALGORITHM` | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | Access token lifetime in minutes |
| `NEW_ACCESS_TOKEN_EXPIRE_MINUTES` | `120` | Access token lifetime issued on refresh |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | `1440` | Refresh token lifetime in minutes |
| `redis_url` | `redis://localhost:6379/0` | Redis connection URL |
| `RATE_LIMIT_ENABLED` | `true` | Toggle rate limiting globally |
| `TRUSTED_PROXY` | `false` | Trust `X-Forwarded-For` for client IP resolution |
| `STATIC_HOST` | `http://localhost:8001` | Base URL for static file serving |
| `SECONDS_TO_SEND_USER_STATUS` | `60` | Interval for broadcasting user online status |

> Replace the JWT secret keys with strong random strings before deploying.

---

## API Reference

All REST endpoints are prefixed with `/api/v1`.

### Authentication — `/api/v1/auth`

| Method | Path | Description |
|---|---|---|
| `POST` | `/register` | Create a new account. Returns user info and sets auth cookies. |
| `POST` | `/login` | Authenticate with email and password. Sets auth cookies. |
| `POST` | `/refresh` | Exchange a valid refresh token for a new access token. |
| `POST` | `/logout` | Clear auth cookies. |
| `GET` | `/me` | Return the currently authenticated user. |

### Users — `/api/v1/users`

| Method | Path | Description |
|---|---|---|
| `GET` | `/search?q=<query>` | Search users by username. |
| `GET` | `/<user_id>` | Retrieve a user profile by ID. |

### Conversations — `/api/v1/conversations`

| Method | Path | Description |
|---|---|---|
| `POST` | `/` | Create a new one-on-one conversation. |
| `GET` | `/` | List all conversations for the authenticated user. |

### Messages — `/api/v1/messages`

| Method | Path | Description |
|---|---|---|
| `GET` | `/<conversation_id>` | Fetch message history for a conversation. |

---

## WebSocket Protocol

Connect to `ws://localhost:8000/v1/realtime/ws` with the `access_token` cookie present. The server authenticates the connection before accepting it. If authentication fails the socket is closed immediately.

Upon successful connection the server sends a `ready` frame:

```json
{
  "type": "ready",
  "user_id": "<uuid>",
  "conversations": ["<conv-uuid>", "..."]
}
```

### Client-to-Server Events

| `type` | Required fields | Description |
|---|---|---|
| `ping` | — | Keep-alive. Server replies with `{"type": "pong"}`. |
| `message:send` | `conversation_id`, `content`, `temp_id` | Send a message to a conversation. |
| `typing:start` | `conversation_id` | Notify other members that the user is typing. |
| `typing:stop` | `conversation_id` | Notify other members that the user stopped typing. |
| `message:read` | `conversation_id` | Mark all messages in a conversation as read. |

### Server-to-Client Events

| `type` | Payload fields | Description |
|---|---|---|
| `message:ack` | `temp_id`, `message` | Confirms a sent message back to the sender. Replaces the optimistic entry. |
| `message:new` | `message` | Delivers a new message to all other members of the conversation. |
| `typing:update` | `conversation_id`, `user_id`, `username`, `is_typing` | Typing status change from another member. |
| `conversation:new` | `id`, `other_username` | A new conversation was started by another user. |
| `read:update` | `conversation_id`, `user_id` | A member has marked the conversation as read. |
| `error` | `detail` | Describes a problem caused by the previous client frame. |

---

## Rate Limiting

Rate limits are enforced per IP address (or per authenticated user) using a Redis sliding-window counter. All limits reset within the stated time window.

| Endpoint group | Limit |
|---|---|
| `auth:register` | 3 requests per hour |
| `auth:login` | 5 requests per minute |
| `auth:refresh` | 30 requests per hour |
| User search | 60 requests per minute |
| User get | 120 requests per minute |
| Conversation create | 20 requests per minute |
| Conversation list | 120 requests per minute |
| Message send | 30 requests per minute |
| Message history | 120 requests per minute |
| Message read | 120 requests per minute |
| Global HTTP (coarse cap) | 300 requests per minute |

---

## Database Models

### User

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `username` | String(20) | Unique |
| `name` | String(20) | Optional display name |
| `email` | String(120) | Unique |
| `hashed_password` | String(255) | bcrypt hash |
| `last_seen` | DateTime (tz) | Defaults to creation time |

### Conversation

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `pair_key` | String | Unique key derived from the two member IDs; prevents duplicate conversations |
| `is_read` | Boolean | Overall read status |
| `created_at` | DateTime (tz) | |
| `updated_at` | DateTime (tz) | Indexed; used to sort the conversation list by most recent activity |

### Member

| Column | Type | Notes |
|---|---|---|
| `conversation_id` | UUID | FK to Conversation (composite primary key) |
| `user_id` | UUID | FK to User (composite primary key) |
| `joined_at` | DateTime (tz) | |
| `last_read_at` | DateTime (tz) | Nullable; tracks the per-member read position |

### Message

| Column | Type | Notes |
|---|---|---|
| `id` | UUID | Primary key |
| `conversation_id` | UUID | FK to Conversation |
| `sender_id` | UUID | FK to User |
| `content` | String(1000) | |
| `message_type` | String(20) | Defaults to `"text"` |
| `is_read` | Boolean | |
| `is_deleted` | Boolean | Soft-delete flag |
| `deleted_at` | DateTime (tz) | Nullable; set when the message is soft-deleted |
| `created_at` | DateTime (tz) | Indexed |
