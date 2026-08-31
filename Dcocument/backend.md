# Chatify Backend Documentation

## Table of Contents

1. [Overview](#overview)
2. [Technology Stack](#technology-stack)
3. [Project Structure](#project-structure)
4. [Architecture](#architecture)
5. [Database Models](#database-models)
6. [Module Documentation](#module-documentation)
7. [API Reference](#api-reference)
8. [Configuration](#configuration)
9. [Current Progress](#current-progress)
10. [Known Issues and Technical Debt](#known-issues-and-technical-debt)
11. [What to Add Next](#what-to-add-next)

---

## Overview

Chatify is a real-time chat application. The backend is a Python asynchronous REST and WebSocket API built with FastAPI. It handles user authentication, conversation management, message persistence, and live message delivery over WebSocket connections. The database layer uses SQLAlchemy's async engine backed by SQLite for local development.

---

## Technology Stack

| Component         | Library / Tool                          |
|-------------------|-----------------------------------------|
| Web framework     | FastAPI                                 |
| Async ORM         | SQLAlchemy (async) + aiosqlite          |
| Data validation   | Pydantic v2 + pydantic-settings         |
| Authentication    | JWT via python-jose, bcrypt via passlib |
| Database          | SQLite (development), configurable      |
| WebSocket support | FastAPI native WebSocket                |
| ASGI server       | Uvicorn                                 |

---

## Project Structure

```
backend/
├── .env                      # Environment variables (not committed)
├── .gitignore
├── database.db               # SQLite database file (not committed)
└── src/
    ├── main.py               # Application entry point, router registration, lifespan
    ├── config.py             # Settings loaded from .env via pydantic-settings
    ├── database.py           # Async SQLAlchemy engine, session factory, BaseModel
    ├── model.py              # All ORM models: User, Conversession, Member, Message
    ├── dependences.py        # Shared FastAPI dependencies (get_user)
    ├── utils.py              # Password hashing utilities
    ├── authentication/
    │   ├── schemas.py        # Pydantic schemas: UserRequest, LoginRequest, UserResponse
    │   ├── reposetory.py     # UserRepository: DB queries for the User model
    │   ├── service.py        # AuthService: register, login, refresh logic
    │   ├── utiles.py         # JWT creation and verification helpers
    │   └── routes.py         # Auth router: /auth endpoints
    ├── chat/
    │   ├── schemas.py        # Pydantic schemas for conversations and messages
    │   ├── ConversessionReposetory.py   # DB queries for Conversession and Member models
    │   ├── ConversessionService.py      # Business logic for conversations
    │   ├── ConversessionRoutes.py       # Conversation router: /conversations
    │   ├── MessageReposetory.py         # DB queries for Message model
    │   ├── MessageService.py            # Business logic for messages
    │   └── MessageRoutes.py             # Message router: /messages
    └── websockets/
        ├── schemas.py        # Pydantic schema: WebSocketMessage
        ├── manager.py        # ConnectionManager: in-memory socket room management
        ├── service.py        # WebSocketManager: connection lifecycle, message handling
        └── routes.py         # WebSocket router: /ws/conversession/{id}
```

---

## Architecture

The backend follows a three-layer architecture within each domain module.

```
HTTP Request / WebSocket Frame
        |
        v
  [ Routes Layer ]
  Handles HTTP/WebSocket input, validates request schemas,
  calls the service layer, and returns response schemas.
        |
        v
  [ Service Layer ]
  Holds all business logic and authorization rules.
  Orchestrates calls to one or more repositories.
        |
        v
  [ Repository Layer ]
  Pure database access. Executes SQLAlchemy queries.
  Returns ORM model instances or None.
        |
        v
  [ SQLAlchemy Async Session ]
  Interfaces with the SQLite database file.
```

### HTTP Request Lifecycle

1. FastAPI receives the request and runs dependency injection.
2. `get_db` yields an `AsyncSession` for the request.
3. `get_user` (where required) reads the `access_token` cookie, verifies the JWT, and fetches the user from the database. A 401 is raised if authentication fails at any step.
4. The route calls the appropriate service method.
5. The service enforces business rules and calls the repository.
6. The repository executes the SQL query and returns an ORM object.
7. The route serializes the ORM object to a Pydantic response schema and returns it.

### WebSocket Lifecycle

1. A client opens a WebSocket connection to `/ws/conversession/{id}`.
2. `WebSocketManager.connect_socket` verifies the conversation exists and that the user is a member, then accepts the socket via `ConnectionManager.connect`.
3. The route enters a receive loop, parsing each text frame as a JSON object validated against `WebSocketMessage`.
4. `WebSocketManager.handel_message` delegates to `MessageService.send_message` to persist the message, then calls `ConnectionManager.broadcast` to push the payload to all sockets in the same room.
5. On disconnect or error, `ConnectionManager.diconnect` removes the socket from the room's active set.

### Connection Room Management

`ConnectionManager` stores active sockets in a plain Python dict keyed by conversation ID:

```
active_connections: dict[str, set[WebSocket]]
```

This is in-process memory only. If the server restarts, all connections are lost. This is not suitable for multi-process deployments without a shared broker such as Redis.

---

## Database Models

All models inherit from `BaseModel` (SQLAlchemy `DeclarativeBase`). Tables are created automatically on application startup via the `lifespan` context manager in `main.py`.

### User

Table: `users`

| Column          | Type         | Constraints                          |
|-----------------|--------------|--------------------------------------|
| id              | UUID         | Primary key, indexed, auto-generated |
| username        | VARCHAR(20)  | Unique, not null                     |
| email           | VARCHAR(120) | Unique, not null                     |
| hashed_password | VARCHAR(255) | Not null                             |
| last_seen       | DateTime     | Not null, server default = now()     |

Relationships: `conversation_memberships` (list of `Member`), `messages` (list of `Message`).

### Conversession

Table: `conversessions`

| Column | Type | Constraints                          |
|--------|------|--------------------------------------|
| id     | UUID | Primary key, indexed, auto-generated |

Relationships: `members` (cascade delete-orphan), `messages` (cascade delete-orphan).

Note: "Conversession" is a persistent typo for "Conversation" that is used consistently throughout the entire codebase. Renaming it would require a database migration.

### Member

Table: `members` (join table between `users` and `conversessions`)

| Column           | Type     | Constraints                             |
|------------------|----------|-----------------------------------------|
| conversession_id | UUID     | Primary key, FK to conversessions.id    |
| user_id          | UUID     | Primary key, FK to users.id             |
| joined_at        | DateTime | Not null, server default = now()        |

Composite primary key on `(conversession_id, user_id)`.

### Message

Table: `messages`

| Column           | Type          | Constraints                               |
|------------------|---------------|-------------------------------------------|
| id               | UUID          | Primary key, indexed, auto-generated      |
| conversession_id | UUID          | FK to conversessions.id, indexed          |
| sender_id        | UUID          | FK to users.id, indexed                   |
| content          | VARCHAR(1000) | Not null                                  |
| created_at       | DateTime      | Not null, server default = now(), indexed |
| is_deleted       | Boolean       | Not null, default = False                 |
| deleted_at       | DateTime      | Nullable                                  |

Messages are soft-deleted: `is_deleted` is set to `True` and `deleted_at` is recorded rather than removing the row from the database.

---

## Module Documentation

### Core

#### `src/main.py`

Application entry point. Registers all routers and configures CORS middleware. Uses an `asynccontextmanager` lifespan function to run `BaseModel.metadata.create_all` on startup, creating all tables if they do not exist.

Registered routers:

| Prefix           | Module                       |
|------------------|------------------------------|
| `/auth`          | `authentication.routes`      |
| `/conversations` | `chat.ConversessionRoutes`   |
| `/messages`      | `chat.MessageRoutes`         |
| `/ws`            | `websockets.routes`          |

CORS is configured but `allow_origins` is currently a hardcoded string pointing to the local test file rather than reading from settings.

#### `src/config.py`

Uses `pydantic-settings` to load configuration from a `.env` file located in the `src/` directory. The `get_settings()` factory returns a `DevelopmentSettings` instance, which extends `GlobalSettings` without any overrides.

Key configuration values:

| Setting                       | Default                             | Description                              |
|-------------------------------|-------------------------------------|------------------------------------------|
| `DATABASE_URL`                | `sqlite+aiosqlite:///./database.db` | Async database connection string         |
| `JWT_ACCESS_SECRET_KEY`       | hardcoded string                    | Secret for signing access tokens         |
| `JWT_REFRESH_SECRET_KEY`      | hardcoded string                    | Secret for signing refresh tokens        |
| `ENCRYPTION_ALGORITHM`        | `HS256`                             | JWT signing algorithm                    |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                                | Access token lifetime in minutes         |
| `REFRESH_TOKEN_EXPIRE_MINUTES`| `1440`                              | Refresh token lifetime (24 hours)        |
| `SECONDS_TO_SEND_USER_STATUS` | `60`                                | Reserved for a future presence feature   |

The JWT secret keys are hardcoded defaults and must be overridden in `.env` before any deployment.

#### `src/database.py`

Creates the async SQLAlchemy engine and session factory.

- `engine`: Async engine built from `DATABASE_URL` with SQL echo enabled.
- `SessionLocal`: `async_sessionmaker` bound to the engine, `expire_on_commit=False`.
- `get_db()`: Async generator that yields an `AsyncSession`. Used as a FastAPI `Depends` dependency.

#### `src/model.py`

Defines all four ORM models (`User`, `Conversession`, `Member`, `Message`). See Database Models section for full column details.

#### `src/dependences.py`

Contains `get_user`, the primary shared authentication dependency used by all protected endpoints.

- Reads the `access_token` cookie.
- Decodes and validates the JWT using `verify_access_token`.
- Parses the `sub` claim as a UUID and fetches the corresponding `User` from the database.
- Raises `HTTP 401 Unauthorized` at any failure point with a descriptive error message.

#### `src/utils.py`

Password utilities using `passlib` with the `bcrypt` scheme.

- `get_hashed_password(password: str) -> str`: Hashes a plain-text password.
- `verify_password(plain: str, hashed: str) -> bool`: Compares a plain-text password to a stored hash.

---

### Authentication Module

Router prefix: `/auth`

#### `authentication/schemas.py`

| Schema         | Fields                              | Validation rules                   |
|----------------|-------------------------------------|------------------------------------|
| `UserRequest`  | `username`, `email`, `password`     | username 3-20 chars, password 8-70 |
| `LoginRequest` | `email`, `password`                 | password 8-128 chars               |
| `UserResponse` | `user_id` (UUID4), `username`, `email` | Response schema, no input          |

#### `authentication/reposetory.py` - `UserRepository`

| Method              | Parameters             | Returns        |
|---------------------|------------------------|----------------|
| `get_user_by_email` | `db`, `email`          | `User` or None |
| `get_user_by_id`    | `db`, `user_id` (UUID) | `User` or None |
| `get_user_by_name`  | `db`, `username`       | `User` or None |
| `create_user`       | `db`, `user`           | `User`         |

#### `authentication/service.py` - `AuthService`

| Method                | Summary                                                                        |
|-----------------------|--------------------------------------------------------------------------------|
| `register_user`       | Checks for duplicate username and email, hashes password, creates `User` row.  |
| `login_user`          | Finds user by email, verifies bcrypt password, issues access and refresh JWTs. |
| `refresh_access_token`| Verifies the refresh JWT, fetches user, issues a new access JWT.               |

#### `authentication/utiles.py`

JWT utility functions. All tokens contain `sub` (user ID as string), `exp` (expiry timestamp), and `type` (`"access"` or `"refresh"`).

| Function               | Description                                                |
|------------------------|------------------------------------------------------------|
| `create_access_token`  | Creates a signed JWT with type `"access"`.                 |
| `create_refresh_token` | Creates a signed JWT with type `"refresh"`.                |
| `verify_access_token`  | Decodes an access token. Returns payload dict or None.     |
| `verify_refresh_token` | Decodes a refresh token. Returns payload dict or None.     |

#### `authentication/routes.py`

| Endpoint         | Method | Auth | Description                                              |
|------------------|--------|------|----------------------------------------------------------|
| `/auth/register` | POST   | No   | Creates a new user account. Returns `UserResponse`.      |
| `/auth/login`    | POST   | No   | Authenticates user and sets HttpOnly cookies.            |
| `/auth/refresh`  | POST   | No   | Issues a new access token from a valid refresh cookie.   |
| `/auth/logout`   | POST   | No   | Deletes both auth cookies from the browser.              |
| `/auth/me`       | GET    | Yes  | Returns the currently authenticated user's profile.      |

Cookies set on login:

| Cookie          | Max-Age | HttpOnly | Secure |
|-----------------|---------|----------|--------|
| `access_token`  | 1 hour  | Yes      | No     |
| `refresh_token` | 30 days | Yes      | No     |

`secure=False` is intentional for local HTTP development and must be changed to `True` in production.

---

### Chat Module - Conversations

Router prefix: `/conversations`

#### Schemas (Conversation)

| Schema                 | Fields                         | Notes               |
|------------------------|--------------------------------|---------------------|
| `ConversationCreate`   | `user_ids: list[UUID]`         | Minimum 1 UUID      |
| `ConversationResponse` | `id: UUID`                     | ORM mode enabled    |

#### `chat/ConversessionReposetory.py` - `ConversessionReposetory`

| Method                  | Description                                             |
|-------------------------|---------------------------------------------------------|
| `create_conversession`  | Adds a `Conversession` to the session and flushes.      |
| `get_converssion_by_id` | Fetches a conversation by UUID.                         |
| `add_member`            | Adds a `Member` row to the session and flushes.         |
| `get_member`            | Fetches a `Member` by user_id and conversession_id.     |

#### `chat/ConversessionService.py` - `ConversessionService`

| Method                 | Description                                                                    |
|------------------------|--------------------------------------------------------------------------------|
| `create_conversession` | Creates a `Conversession`, iterates user_ids and adds each as a `Member` row.  |
| `get_conversession`    | Delegates to repository lookup by ID.                                          |
| `is_member`            | Returns True if a `Member` row exists for the given user and conversation.     |

#### `chat/ConversessionRoutes.py`

| Endpoint                  | Method | Auth | Description                                                        |
|---------------------------|--------|------|--------------------------------------------------------------------|
| `/conversations`          | POST   | Yes  | Creates a conversation. The authenticated user is auto-included.   |
| `/conversations/{id}`     | GET    | Yes  | Returns a conversation if the authenticated user is a member.      |

---

### Chat Module - Messages

Router prefix: `/messages`

#### Schemas (Message)

| Schema            | Fields                                                                                  |
|-------------------|-----------------------------------------------------------------------------------------|
| `MessageCreate`   | `content: str` (1-1000 chars)                                                           |
| `MessageResponse` | `id`, `conversession_id`, `sender_id`, `content`, `created_at`, `is_deleted`, `deleted_at` |

#### `chat/MessageReposetory.py` - `MessageReposetory`

| Method              | Description                                                                        |
|---------------------|------------------------------------------------------------------------------------|
| `create_message`    | Adds message to session, flushes, refreshes, and returns the persisted instance.   |
| `get_message_by_id` | Fetches a single message by UUID.                                                  |
| `get_all_messages`  | Returns up to `limit` (default 50) non-deleted messages, ordered newest-first.     |
| `delete_message`    | Soft-deletes by setting `is_deleted=True` and `deleted_at=func.now()`, then flushes. |

`update_message` is not yet implemented in this repository class even though the service and route call it.

#### `chat/MessageService.py` - `MessageService`

| Method           | Description                                                                                      |
|------------------|--------------------------------------------------------------------------------------------------|
| `send_message`   | Verifies conversation exists and sender is a member, then creates and commits the message.       |
| `get_messages`   | Verifies conversation and membership before returning the message list.                          |
| `delete_message` | Verifies message exists, that the requestor is the sender, and that it is not already deleted.   |
| `update_message` | Verifies message exists, sender ownership, and that it is not deleted. Calls repo to update.     |

#### `chat/MessageRoutes.py`

| Endpoint                                       | Method | Auth | Description                          |
|------------------------------------------------|--------|------|--------------------------------------|
| `/messages/conversations/{conversession_id}`   | POST   | Yes  | Sends a new message.                 |
| `/messages/conversations/{conversession_id}`   | GET    | Yes  | Retrieves messages in a conversation.|
| `/messages/{message_id}`                       | PATCH  | Yes  | Edits the content of a message.      |
| `/messages/{message_id}`                       | DELETE | Yes  | Soft-deletes a message.              |

---

### WebSocket Module

Router prefix: `/ws`

#### `websockets/schemas.py`

| Schema             | Fields                                |
|--------------------|---------------------------------------|
| `WebSocketMessage` | `type: str`, `content: str` (1-1000)  |

#### `websockets/manager.py` - `ConnectionManager`

Manages in-memory WebSocket rooms as a `dict[str, set[WebSocket]]`.

| Method      | Description                                                              |
|-------------|--------------------------------------------------------------------------|
| `connect`   | Accepts the WebSocket and adds it to the conversation room's set.        |
| `diconnect` | Removes a WebSocket from the room's set on disconnect. (Typo in name.)   |
| `broadcast` | Sends a JSON payload to every WebSocket currently in the given room.     |

#### `websockets/service.py` - `WebSocketManager`

| Method                | Description                                                                     |
|-----------------------|---------------------------------------------------------------------------------|
| `connect_socket`      | Verifies conversation and membership. Closes socket with code 1008 if invalid. |
| `handel_message`      | Persists the message via `MessageService`, then broadcasts to the room.         |
| `websocket_disconnect`| Delegates to `ConnectionManager.diconnect`.                                     |

#### `websockets/routes.py`

| Endpoint                               | Protocol  | Auth           | Description                          |
|----------------------------------------|-----------|----------------|--------------------------------------|
| `/ws/conversession/{conversession_id}` | WebSocket | Hardcoded UUID | Real-time message send and receive.  |

WebSocket authentication is not implemented. The user ID is currently a hardcoded fixed UUID inside the route handler.

---

## API Reference

### Base URL

```
http://localhost:8000
```

### Authentication

```
POST   /auth/register
POST   /auth/login
POST   /auth/refresh
POST   /auth/logout
GET    /auth/me
```

### Conversations

```
POST   /conversations
GET    /conversations/{conversation_id}
```

### Messages

```
POST   /messages/conversations/{conversession_id}
GET    /messages/conversations/{conversession_id}
PATCH  /messages/{message_id}
DELETE /messages/{message_id}
```

### WebSocket

```
WS     /ws/conversession/{conversession_id}
```

#### Client-to-Server Frame Format

```json
{
  "type": "message",
  "content": "Hello, world!"
}
```

#### Server-to-All-Clients Broadcast Format

```json
{
  "type": "message",
  "data": {
    "id": "<uuid>",
    "conversession_id": "<uuid>",
    "sender_id": "<uuid>",
    "content": "Hello, world!",
    "created_at": "2026-08-31T09:00:00"
  }
}
```

---

## Configuration

Create a `.env` file inside the `src/` directory:

```env
ENVIRONMENT=development
DATABASE_URL=sqlite+aiosqlite:///./database.db
JWT_ACCESS_SECRET_KEY=<replace-with-a-strong-random-key>
JWT_REFRESH_SECRET_KEY=<replace-with-a-different-strong-random-key>
ENCRYPTION_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_MINUTES=1440
ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

### Running the Development Server

```bash
uvicorn src.main:app --reload
```

Interactive API documentation is available at `http://localhost:8000/docs`.

---

## Current Progress

### Completed

- Full user authentication flow: register, login, logout, token refresh, and current-user endpoint.
- JWT-based stateless authentication using HttpOnly cookies for both access and refresh tokens.
- Separate access and refresh token secrets with type-checked payloads to prevent token confusion attacks.
- Soft-delete support on messages using `is_deleted` and `deleted_at` columns.
- Conversation creation with automatic membership enforcement (at least two distinct members required).
- Message CRUD: send, read history, edit content, and soft-delete, all with ownership verification.
- Real-time messaging via WebSocket with in-memory room-based broadcasting.
- WebSocket connection authorization: conversation existence and user membership are verified before the socket is accepted.
- Async SQLite database with automatic table creation on application startup.
- Layered architecture (routes, service, repository) applied consistently across all three domain modules.
- Centralized configuration management using `pydantic-settings` and `.env`.

### Partially Complete

- **WebSocket authentication**: Conversation membership is validated, but the user identity is a hardcoded UUID instead of being derived from a token or cookie.
- **CORS configuration**: Middleware is active but `allow_origins` is a hardcoded test URL instead of reading from `settings.ALLOWED_ORIGINS`.
- **Message editing**: The route (`PATCH /messages/{id}`) and service method (`update_message`) are in place, but `MessageReposetory.update_message` is not implemented, so calling this endpoint will raise an `AttributeError`.

---

## Known Issues and Technical Debt

| Issue | File | Severity |
|-------|------|----------|
| WebSocket user ID is hardcoded to a fixed UUID | `websockets/routes.py` lines 70-72 | High |
| `MessageReposetory.update_message` method is missing | `chat/MessageReposetory.py` | High |
| JWT secret keys are hardcoded defaults in `config.py` | `src/config.py` lines 27-28 | High |
| `delete_message` in the repository returns `bool` but callers expect a `Message` object | `chat/MessageReposetory.py` | Medium |
| `allow_origins` in CORS middleware is a plain string, not a list | `src/main.py` line 33 | Medium |
| `secure=False` on auth cookies; must be `True` in production over HTTPS | `authentication/routes.py` | Medium |
| Typo "Conversession" (instead of "Conversation") used as table name and throughout all related files | Entire codebase | Low |
| Typo "reposetory" in all repository file names and class names | Entire codebase | Low |
| Typo `diconnect` (missing 's') in `ConnectionManager` | `websockets/manager.py` line 26 | Low |
| `get_all_messages` returns messages newest-first; this may be unexpected for a chat history feed | `chat/MessageReposetory.py` line 57 | Low |
| Debug `print()` statements scattered throughout the codebase | Multiple files | Low |
| `MessageReposetory` imports `FastAPI` which is never used | `chat/MessageReposetory.py` line 1 | Low |

---

## What to Add Next

The following are recommended additions, ordered by priority.

### 1. WebSocket Authentication

The WebSocket endpoint must derive the user identity from a token rather than a hardcoded UUID. Two options:

- Read the `access_token` cookie during the handshake: `websocket.cookies.get("access_token")`.
- Accept a short-lived token as a query parameter: `ws://host/ws/conversession/{id}?token=<jwt>`.

### 2. Implement `MessageReposetory.update_message`

The PATCH endpoint for editing messages will raise `AttributeError` until this method exists. A correct implementation:

```python
async def update_message(
    self,
    db: AsyncSession,
    message_id: uuid.UUID,
    content: str,
) -> Message:
    result = await db.execute(
        select(Message).where(Message.id == message_id)
    )
    message = result.scalar_one_or_none()
    if message:
        message.content = content
        await db.flush()
        await db.refresh(message)
    return message
```

### 3. Fix the Delete Message Return Value

`MessageReposetory.delete_message` returns a `bool`, but `MessageService` passes the result directly to the route which expects a `Message` object. Update the repository method to return the updated `Message` instance after soft-deletion.

### 4. Move CORS Origins to Settings

Replace the hardcoded string in `main.py`:

```python
allow_origins=settings.ALLOWED_ORIGINS.split(","),
```

### 5. User Search Endpoint

Users currently have no way to find other users by name or email in order to start a conversation. Without this, the frontend cannot obtain the UUID required by `ConversationCreate.user_ids`.

Suggested endpoint:

```
GET /users/search?q=<query>
```

Returns a list of `UserResponse` objects matching the query against `username` or `email`.

### 6. List All Conversations for a User

A user needs to retrieve all conversations they belong to. This requires a query joining `members` to `conversessions` filtered by the authenticated user's ID.

Suggested endpoint:

```
GET /conversations
```

### 7. User Presence and Online Status

The `SECONDS_TO_SEND_USER_STATUS` setting is defined but not used. Implement basic presence:

- Update `User.last_seen` on authenticated requests or on each WebSocket message received.
- Broadcast a presence event when a user connects to or disconnects from a room.

### 8. Message Pagination

`get_all_messages` uses a hardcoded `limit=50` with no cursor or offset support. Add proper pagination to the GET messages endpoint:

```
GET /messages/conversations/{id}?limit=50&before=<message_id>
```

### 9. Secure Environment Secrets

Remove the hardcoded JWT key defaults from `config.py` and add an `.env.example` file to the repository documenting every required variable. Rotate any existing tokens once this is done.

### 10. Replace Print Statements with Logging

Remove all `print()` calls and replace them with Python's `logging` module. The commented-out `LOGGING_CONFIG` block at the bottom of `config.py` provides a working starting point.

### 11. Switch to PostgreSQL for Production

`config.py` already contains commented-out PostgreSQL configuration fields. Create a `ProductionSettings` class that reads `DATABASE_URL` from environment variables and uses an async PostgreSQL driver such as `asyncpg`.

### 12. Add Alembic for Database Migrations

The current `create_all` approach cannot handle schema changes on a database that already has data. Add Alembic to manage incremental migrations:

```bash
pip install alembic
alembic init migrations
```

This becomes essential before any production deployment or once the schema needs to evolve after the initial release.
