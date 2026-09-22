import asyncio
import logging
import uuid
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

class Manager :

    def __init__(
        self
    ) -> None :

        self._user_socket : dict[uuid.UUID , set[WebSocket]] = defaultdict(set)
        self._conversation_rooms : dict[uuid.UUID , set[uuid.UUID]] = defaultdict(set)
        self._lock = asyncio.Lock()

    # lifecycle
    async def connect(
        self,
        user_id : uuid.UUID,
        ws : WebSocket
    ) -> None :

        async with self._lock :
            self._user_socket[user_id].add(ws)

    async def disconnect(
        self,
        user_id : uuid.UUID,
        ws : WebSocket
    ) -> None :

        async with self._lock :
            socket = self._user_socket.get(user_id)

            if not socket :
                return

            socket.discard(ws)
            if not socket :
                del self._user_socket[user_id]
                for members in self._conversation_rooms.values() :
                    members.discard(user_id)

    async def is_online(
        self,
        user_id : uuid.UUID
    ) -> bool :

        async with self._lock :
            return bool(self._user_socket.get(user_id))


    # rooms
    async def join_conversation(
        self,
        user_id : uuid.UUID,
        conversation_ids : list[uuid.UUID]
    ) -> None :

        async with self._lock :
            for cid in conversation_ids :
                self._conversation_rooms[cid].add(user_id)

    async def leave_rooms(
        self,
        user_id : uuid.UUID,
        conversation_id : uuid.UUID
    ) -> None :

        async with self._lock :
            self._conversation_rooms[conversation_id].discard(user_id)

    async def members_of (
        self,
        conversation_id : uuid.UUID
    ) -> set[uuid.UUID] :

        async with self._lock :
            return set(self._conversation_rooms.get(conversation_id , set()))


    #delevary

    async def send_to_user(
        self,
        user_id: uuid.UUID,
        payload: dict[str, Any]
    ) -> None:

        async with self._lock:
            sockets = list(self._user_socket.get(user_id, set()))
        await self._send_to_socket(sockets, payload)

    async def broadcast_to_conversation(
        self,
        conversation_id : uuid.UUID,
        payload : dict[str , Any],
        user_id : uuid.UUID | None = None,
    ) -> None :

        members = await self.members_of(
            conversation_id
        )
        if user_id is not None :
            members.discard(user_id)

        async with self._lock:
            targets : list[WebSocket] =[]
            for uid in members :
                targets.extend(self._user_socket.get(uid , set()))
        await self._send_to_socket(targets , payload)

    async def _send_to_socket(
        self,
        sockets : list[WebSocket],
        payload : dict[str , Any]
    ) -> None :

        await asyncio.gather(
            *(self._safe_send(ws,payload) for ws in sockets),
            return_exceptions=True
        )


    @staticmethod
    async def _safe_send(
        ws : WebSocket,
        payload : dict[str , Any]
    ) -> None :

        try :
            await ws.send_json(payload)
        except Exception:
            logger.exception("Failed to send WebSocket message")

manager = Manager()
