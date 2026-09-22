"""
Unit tests for backend/src/realtime/ — Manager + Handler.

Run with:
    cd test && python -m pytest test_realtime.py -v
"""
import asyncio
import uuid
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# We test Manager and Handler in complete isolation (no FastAPI, no DB).
# ---------------------------------------------------------------------------

# ========================== helpers ========================================

def _make_user(user_id: uuid.UUID | None = None, username: str = "alice") -> SimpleNamespace:
    """Create a minimal user-like object."""
    return SimpleNamespace(
        id=user_id or uuid.uuid4(),
        username=username,
    )


def _make_message(
    conversation_id: uuid.UUID | None = None,
    sender_id: uuid.UUID | None = None,
) -> SimpleNamespace:
    """Create a minimal message-like object returned by MessageService.create_message."""
    return SimpleNamespace(
        id=uuid.uuid4(),
        conversation_id=conversation_id or uuid.uuid4(),
        sender_id=sender_id or uuid.uuid4(),
        content="hello",
        message_type="text",
        created_at=datetime.now(timezone.utc),
        is_deleted=False,
    )


def _fake_ws() -> AsyncMock:
    """Return an AsyncMock that behaves like a FastAPI WebSocket."""
    ws = AsyncMock()
    ws.send_json = AsyncMock()
    return ws


# ========================== Manager tests ==================================

# Import here so the module-level `manager` singleton doesn't interfere.
# We instantiate fresh Manager objects in each test.

import sys, os
# Add backend/ so `src.*` imports inside the source files resolve.
# Add backend/src/ so we can import `realtime.manager`, `realtime.handler` directly.
_test_dir = os.path.dirname(os.path.abspath(__file__))
_backend_dir = os.path.join(_test_dir, "..", "backend")
_src_dir = os.path.join(_backend_dir, "src")
for _p in (_backend_dir, _src_dir):
    _p = os.path.normpath(_p)
    if _p not in sys.path:
        sys.path.insert(0, _p)

# Manager only depends on fastapi + asyncio — import directly.
from realtime.manager import Manager

# Handler imports pull in the entire app (database.py creates an engine at module
# level that requires aiosqlite).  We stub the heavy leaf modules so the handler
# module can be imported without any DB driver.
from unittest.mock import MagicMock as _MagicMock
from types import ModuleType as _ModuleType

def _stub_module(name: str, package: bool = False) -> _ModuleType:
    """Create and register a stub module in sys.modules if not already present."""
    if name not in sys.modules:
        mod = _ModuleType(name)
        if package:
            mod.__path__ = []  # make it a package
        # Add common names that the source files import
        mod.__dict__.setdefault("BaseModel", type("BaseModel", (), {}))
        mod.__dict__.setdefault("get_db", lambda: None)
        mod.__dict__.setdefault("User", type("User", (), {}))
        mod.__dict__.setdefault("Conversation", type("Conversation", (), {}))
        mod.__dict__.setdefault("Member", type("Member", (), {}))
        mod.__dict__.setdefault("Message", type("Message", (), {}))
        mod.__dict__.setdefault("resolve_user_from_token", AsyncMock())
        mod.__dict__.setdefault("UserRepo", _MagicMock)
        mod.__dict__.setdefault("UserService", _MagicMock)
        mod.__dict__.setdefault("UserRepository", _MagicMock)
        mod.__dict__.setdefault("verify_access_token", lambda *a, **kw: None)
        mod.__dict__.setdefault("ConversetionRepo", _MagicMock)
        mod.__dict__.setdefault("ConversationService", _MagicMock)
        mod.__dict__.setdefault("MessageRepo", _MagicMock)
        mod.__dict__.setdefault("MessageService", _MagicMock)
        mod.__dict__.setdefault("CreateMessage", _MagicMock)
        mod.__dict__.setdefault("MessageOut", _MagicMock)
        mod.__dict__.setdefault("Messages", _MagicMock)
        sys.modules[name] = mod
    return sys.modules[name]

# Step 1: Stub all heavy modules BEFORE importing handler.
# Mark parent modules as packages so sub-imports work.
_stub_module("src", package=True)
_stub_module("src.database")
_stub_module("src.model")
_stub_module("src.dependences")
_stub_module("src.converseation", package=True)
_stub_module("src.converseation.reposetory")
_stub_module("src.converseation.service")
_stub_module("src.message", package=True)
_stub_module("src.message.reposetory")
_stub_module("src.message.service")
_stub_module("src.message.schemas")
_stub_module("src.user", package=True)
_stub_module("src.user.reposetory")
_stub_module("src.user.service")
_stub_module("src.authentication", package=True)
_stub_module("src.authentication.reposetory")
_stub_module("src.authentication.utiles")
_stub_module("src.config")
_stub_module("src.utils")

# Step 2: Map src.realtime.* to the *real* realtime modules (already importable
# because backend/src is on sys.path).
import realtime.manager as _real_manager_mod
import realtime.schemas as _real_schemas_mod

_rt_pkg = _stub_module("src.realtime", package=True)
sys.modules["src.realtime.manager"] = _real_manager_mod
sys.modules["src.realtime.schemas"] = _real_schemas_mod
_rt_pkg.manager = _real_manager_mod
_rt_pkg.schemas = _real_schemas_mod

# Now we can safely import the handler module
from realtime.handler import RealTimeHandler  # noqa: E402


class TestManagerConnectDisconnect:
    """Bug 7 (rename) + general lifecycle."""

    @pytest.mark.asyncio
    async def test_connect_adds_socket(self):
        m = Manager()
        uid = uuid.uuid4()
        ws = _fake_ws()

        await m.connect(uid, ws)

        assert ws in m._user_socket[uid]

    @pytest.mark.asyncio
    async def test_disconnect_removes_socket(self):
        m = Manager()
        uid = uuid.uuid4()
        ws = _fake_ws()

        await m.connect(uid, ws)
        await m.disconnect(uid, ws)

        assert uid not in m._user_socket

    @pytest.mark.asyncio
    async def test_disconnect_cleans_rooms(self):
        """When the last socket disconnects, the user is removed from all rooms."""
        m = Manager()
        uid = uuid.uuid4()
        ws = _fake_ws()
        cid = uuid.uuid4()

        await m.connect(uid, ws)
        await m.join_conversation(uid, [cid])

        assert uid in m._conversation_rooms[cid]

        await m.disconnect(uid, ws)

        assert uid not in m._conversation_rooms.get(cid, set())

    @pytest.mark.asyncio
    async def test_disconnect_noop_for_unknown_user(self):
        """Disconnecting an unknown user should not raise."""
        m = Manager()
        ws = _fake_ws()
        await m.disconnect(uuid.uuid4(), ws)  # no error


class TestManagerIsOnline:

    @pytest.mark.asyncio
    async def test_online_after_connect(self):
        m = Manager()
        uid = uuid.uuid4()
        ws = _fake_ws()

        await m.connect(uid, ws)
        assert await m.is_online(uid) is True

    @pytest.mark.asyncio
    async def test_offline_after_disconnect(self):
        m = Manager()
        uid = uuid.uuid4()
        ws = _fake_ws()

        await m.connect(uid, ws)
        await m.disconnect(uid, ws)
        assert await m.is_online(uid) is False


class TestManagerRooms:

    @pytest.mark.asyncio
    async def test_join_and_members_of(self):
        m = Manager()
        uid = uuid.uuid4()
        cid = uuid.uuid4()

        await m.join_conversation(uid, [cid])
        members = await m.members_of(cid)
        assert uid in members

    @pytest.mark.asyncio
    async def test_leave_rooms(self):
        m = Manager()
        uid = uuid.uuid4()
        cid = uuid.uuid4()

        await m.join_conversation(uid, [cid])
        await m.leave_rooms(uid, cid)
        members = await m.members_of(cid)
        assert uid not in members


class TestManagerSendToUser:
    """Bug 5: send_to_user must hold the lock."""

    @pytest.mark.asyncio
    async def test_send_to_user_delivers_payload(self):
        m = Manager()
        uid = uuid.uuid4()
        ws = _fake_ws()

        await m.connect(uid, ws)
        payload = {"type": "hello"}

        await m.send_to_user(uid, payload)

        ws.send_json.assert_awaited_once_with(payload)

    @pytest.mark.asyncio
    async def test_send_to_user_no_sockets(self):
        """Sending to a user with no sockets should not raise."""
        m = Manager()
        await m.send_to_user(uuid.uuid4(), {"type": "x"})


class TestManagerBroadcast:
    """Bug 6: broadcast reads _user_socket under lock; also tests sender exclusion."""

    @pytest.mark.asyncio
    async def test_broadcast_excludes_sender(self):
        m = Manager()
        sender = uuid.uuid4()
        other = uuid.uuid4()
        cid = uuid.uuid4()

        ws_sender = _fake_ws()
        ws_other = _fake_ws()

        await m.connect(sender, ws_sender)
        await m.connect(other, ws_other)
        await m.join_conversation(sender, [cid])
        await m.join_conversation(other, [cid])

        payload = {"type": "message:new", "content": "hi"}
        await m.broadcast_to_conversation(cid, payload, user_id=sender)

        # Sender should NOT receive the broadcast
        ws_sender.send_json.assert_not_awaited()
        # Other member should receive it
        ws_other.send_json.assert_awaited_once_with(payload)

    @pytest.mark.asyncio
    async def test_broadcast_to_all_when_no_exclude(self):
        m = Manager()
        u1 = uuid.uuid4()
        u2 = uuid.uuid4()
        cid = uuid.uuid4()

        ws1 = _fake_ws()
        ws2 = _fake_ws()

        await m.connect(u1, ws1)
        await m.connect(u2, ws2)
        await m.join_conversation(u1, [cid])
        await m.join_conversation(u2, [cid])

        payload = {"type": "typing:update"}
        await m.broadcast_to_conversation(cid, payload, user_id=None)

        ws1.send_json.assert_awaited_once_with(payload)
        ws2.send_json.assert_awaited_once_with(payload)



def _make_handler(
    user: SimpleNamespace | None = None,
    ws: AsyncMock | None = None,
    conversation_service: AsyncMock | None = None,
    message_service: AsyncMock | None = None,
    db: AsyncMock | None = None,
) -> RealTimeHandler:
    """Factory to build a RealTimeHandler with mock dependencies."""
    return RealTimeHandler(
        ws=ws or _fake_ws(),
        conversation_service=conversation_service or AsyncMock(),
        message_service=message_service or AsyncMock(),
        db=db or AsyncMock(),
        user=user or _make_user(),
    )


class TestDispatch:
    """Bug 1: crash when type is missing."""

    @pytest.mark.asyncio
    async def test_dispatch_missing_type(self):
        ws = _fake_ws()
        h = _make_handler(ws=ws)

        await h.despatch({})  # no "type" key

        ws.send_json.assert_awaited_once()
        payload = ws.send_json.call_args[0][0]
        assert payload["type"] == "error"
        assert "Missing event type" in payload["detail"]

    @pytest.mark.asyncio
    async def test_dispatch_unknown_event(self):
        ws = _fake_ws()
        h = _make_handler(ws=ws)

        await h.despatch({"type": "nonexistent"})

        ws.send_json.assert_awaited_once()
        payload = ws.send_json.call_args[0][0]
        assert payload["type"] == "error"
        assert "Unknown event" in payload["detail"]

    @pytest.mark.asyncio
    async def test_dispatch_routes_to_handler(self):
        ws = _fake_ws()
        h = _make_handler(ws=ws)
        h.on_message_send = AsyncMock()

        data = {"type": "message:send", "conversation_id": str(uuid.uuid4())}
        await h.despatch(data)

        h.on_message_send.assert_awaited_once_with(data)


class TestParseConversationId:
    """Bugs 3 & 4: bad / missing conversation_id."""

    @pytest.mark.asyncio
    async def test_missing_conversation_id(self):
        ws = _fake_ws()
        h = _make_handler(ws=ws)

        result = await h._parse_conversation_id({})

        assert result is None
        ws.send_json.assert_awaited_once()
        assert "Missing conversation_id" in ws.send_json.call_args[0][0]["detail"]

    @pytest.mark.asyncio
    async def test_invalid_conversation_id(self):
        ws = _fake_ws()
        h = _make_handler(ws=ws)

        result = await h._parse_conversation_id({"conversation_id": "not-a-uuid"})

        assert result is None
        ws.send_json.assert_awaited_once()
        assert "Invalid conversation_id" in ws.send_json.call_args[0][0]["detail"]

    @pytest.mark.asyncio
    async def test_valid_conversation_id(self):
        ws = _fake_ws()
        h = _make_handler(ws=ws)
        cid = uuid.uuid4()

        result = await h._parse_conversation_id({"conversation_id": str(cid)})

        assert result == cid
        ws.send_json.assert_not_awaited()


class TestOnMessageSend:

    @pytest.mark.asyncio
    async def test_empty_content_rejected(self):
        ws = _fake_ws()
        h = _make_handler(ws=ws)
        cid = uuid.uuid4()

        await h.on_message_send({
            "conversation_id": str(cid),
            "content": "   ",
            "temp_id": "t1",
        })

        ws.send_json.assert_awaited_once()
        assert ws.send_json.call_args[0][0]["detail"] == "Invalid content"

    @pytest.mark.asyncio
    async def test_non_member_rejected(self):
        ws = _fake_ws()
        conv_svc = AsyncMock()
        conv_svc.is_member = AsyncMock(return_value=False)
        h = _make_handler(ws=ws, conversation_service=conv_svc)
        cid = uuid.uuid4()

        await h.on_message_send({
            "conversation_id": str(cid),
            "content": "hello",
            "temp_id": "t1",
        })

        ws.send_json.assert_awaited_once()
        assert ws.send_json.call_args[0][0]["detail"] == "Not a member"

    @pytest.mark.asyncio
    async def test_success_sends_ack_and_broadcast(self):
        ws = _fake_ws()
        user = _make_user()
        cid = uuid.uuid4()
        msg = _make_message(conversation_id=cid, sender_id=user.id)

        conv_svc = AsyncMock()
        conv_svc.is_member = AsyncMock(return_value=True)

        msg_svc = AsyncMock()
        msg_svc.create_message = AsyncMock(return_value=msg)

        h = _make_handler(ws=ws, user=user, conversation_service=conv_svc, message_service=msg_svc)

        with patch("realtime.handler.manager") as mock_manager:
            mock_manager.send_to_user = AsyncMock()
            mock_manager.broadcast_to_conversation = AsyncMock()

            await h.on_message_send({
                "conversation_id": str(cid),
                "content": "hello",
                "temp_id": "t1",
            })

            # Ack sent to sender
            mock_manager.send_to_user.assert_awaited_once()
            ack_payload = mock_manager.send_to_user.call_args[0][1]
            assert ack_payload["type"] == "message:ack"
            assert ack_payload["temp_id"] == "t1"

            # Broadcast sent to conversation
            mock_manager.broadcast_to_conversation.assert_awaited_once()
            bc_payload = mock_manager.broadcast_to_conversation.call_args.kwargs["payload"]
            assert bc_payload["type"] == "message:new"


class TestOnTypingStop:
    """Bug 2: on_typing_stop must check membership."""

    @pytest.mark.asyncio
    async def test_non_member_blocked(self):
        ws = _fake_ws()
        conv_svc = AsyncMock()
        conv_svc.is_member = AsyncMock(return_value=False)
        h = _make_handler(ws=ws, conversation_service=conv_svc)
        cid = uuid.uuid4()

        with patch("realtime.handler.manager") as mock_manager:
            mock_manager.broadcast_to_conversation = AsyncMock()

            await h.on_typing_stop({
                "conversation_id": str(cid),
            })

            # Should NOT broadcast because the user is not a member
            mock_manager.broadcast_to_conversation.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_member_allowed(self):
        ws = _fake_ws()
        conv_svc = AsyncMock()
        conv_svc.is_member = AsyncMock(return_value=True)
        user = _make_user()
        h = _make_handler(ws=ws, conversation_service=conv_svc, user=user)
        cid = uuid.uuid4()

        with patch("realtime.handler.manager") as mock_manager:
            mock_manager.broadcast_to_conversation = AsyncMock()

            await h.on_typing_stop({
                "conversation_id": str(cid),
            })

            mock_manager.broadcast_to_conversation.assert_awaited_once()
            payload = mock_manager.broadcast_to_conversation.call_args.kwargs["payload"]
            assert payload["type"] == "typing:update"
            assert payload["is_typing"] is False


class TestOnMessageRead:

    @pytest.mark.asyncio
    async def test_message_read_broadcasts(self):
        ws = _fake_ws()
        user = _make_user()
        conv_svc = AsyncMock()
        conv_svc.mark_conversation_read = AsyncMock()
        h = _make_handler(ws=ws, user=user, conversation_service=conv_svc)
        cid = uuid.uuid4()

        with patch("realtime.handler.manager") as mock_manager:
            mock_manager.broadcast_to_conversation = AsyncMock()

            await h.on_message_read({
                "conversation_id": str(cid),
            })

            conv_svc.mark_conversation_read.assert_awaited_once()
            mock_manager.broadcast_to_conversation.assert_awaited_once()
            payload = mock_manager.broadcast_to_conversation.call_args.kwargs["payload"]
            assert payload["type"] == "read:update"
