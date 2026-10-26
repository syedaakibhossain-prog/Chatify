import asyncio
import logging
import uuid
from collections import defaultdict
from typing import Any

from fastapi import WebSocket

logger = logging.getLogger(__name__)

class Manager :
    """
    In-memory WebSocket connection manager.

    Tracks which WebSocket connections belong to each user and which users
    are in which conversation rooms. All state is held in-memory (no Redis),
    so this is single-process only.

    Attributes:
      _user_socket (dict[UUID, set[WebSocket]]): Maps a user UUID to all their active sockets.
      _conversation_rooms (dict[UUID, set[UUID]]): Maps a conversation UUID to the set of
                                                    online user UUIDs currently in that room.
      _lock (asyncio.Lock): Ensures thread-safe mutations of the above dicts.
    """

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
        """
        Registers a new WebSocket connection for a user.

        Parameters:
          user_id (uuid.UUID): The UUID of the connecting user.
          ws (WebSocket)     : The WebSocket connection to register.

        Returns:
          None
        """

        async with self._lock :
            self._user_socket[user_id].add(ws)

    async def disconnect(
        self,
        user_id : uuid.UUID,
        ws : WebSocket
    ) -> None :
        """
        Removes a WebSocket connection for a user.

        If this was the user's last active socket, also removes them from all
        conversation rooms so they no longer receive broadcasts.

        Parameters:
          user_id (uuid.UUID): The UUID of the disconnecting user.
          ws (WebSocket)     : The WebSocket connection to remove.

        Returns:
          None
        """

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
        """
        Checks whether a user currently has at least one active WebSocket connection.

        Parameters:
          user_id (uuid.UUID): The UUID of the user to check.

        Returns:
          bool: True if the user has at least one open socket, False otherwise.
        """

        async with self._lock :
            return bool(self._user_socket.get(user_id))


    # rooms
    # @paramter:user_id - uuid
    # @parameter:conversation_id - uuid
    async def join_conversation(
        self,
        user_id : uuid.UUID,
        conversation_ids : list[uuid.UUID]
    ) -> None :
        """
        Adds a user to one or more conversation rooms so they receive broadcasts.

        Parameters:
          user_id (uuid.UUID)               : The UUID of the user to add to the rooms.
          conversation_ids (list[uuid.UUID]): The list of conversation UUIDs to join.

        Returns:
          None
        """

        async with self._lock :
            for cid in conversation_ids :
                self._conversation_rooms[cid].add(user_id)

    async def leave_rooms(
        self,
        user_id : uuid.UUID,
        conversation_id : uuid.UUID
    ) -> None :
        """
        Removes a user from a specific conversation room.

        Parameters:
          user_id (uuid.UUID)        : The UUID of the user to remove.
          conversation_id (uuid.UUID): The UUID of the conversation room to leave.

        Returns:
          None
        """

        async with self._lock :
            self._conversation_rooms[conversation_id].discard(user_id)

    async def members_of (
        self,
        conversation_id : uuid.UUID
    ) -> set[uuid.UUID] :
        """
        Returns the set of online user UUIDs currently in a conversation room.

        Parameters:
          conversation_id (uuid.UUID): The UUID of the conversation room to inspect.

        Returns:
          set[uuid.UUID]: A snapshot copy of the set of user UUIDs in that room.
        """

        async with self._lock :
            return set(self._conversation_rooms.get(conversation_id , set()))


    #delevary

    async def send_to_user(
        self,
        user_id: uuid.UUID,
        payload: dict[str, Any]
    ) -> None:
        """
        Sends a JSON payload to all active WebSocket connections of a specific user.

        Parameters:
          user_id (uuid.UUID)       : The UUID of the target user.
          payload (dict[str, Any])  : The JSON-serializable message to send.

        Returns:
          None
        """

        async with self._lock:
            sockets = list(self._user_socket.get(user_id, set()))
        await self._send_to_socket(sockets, payload)

    async def broadcast_to_conversation(
        self,
        conversation_id : uuid.UUID,
        payload : dict[str , Any],
        user_id : uuid.UUID | None = None,
    ) -> None :
        """
        Broadcasts a JSON payload to all members of a conversation room,
        optionally excluding a specific user (e.g. the message sender).

        Parameters:
          conversation_id (uuid.UUID)     : The UUID of the target conversation room.
          payload (dict[str, Any])        : The JSON-serializable message to broadcast.
          user_id (uuid.UUID | None)      : If provided, this user is excluded from the broadcast.

        Returns:
          None
        """

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
        """
        Sends a JSON payload concurrently to a list of WebSocket connections.

        Uses asyncio.gather with return_exceptions=True so a failure on one
        socket does not block delivery to the others.

        Parameters:
          sockets (list[WebSocket]) : The list of active WebSocket connections to send to.
          payload (dict[str, Any])  : The JSON-serializable message to send.

        Returns:
          None
        """

        await asyncio.gather(
            *(self._safe_send(ws,payload) for ws in sockets),
            return_exceptions=True
        )


    @staticmethod
    async def _safe_send(
        ws : WebSocket,
        payload : dict[str , Any]
    ) -> None :
        """
        Sends a JSON payload to a single WebSocket connection, swallowing exceptions.

        If the socket is closed or any error occurs during send, the exception is
        logged but not re-raised, ensuring one bad connection does not crash others.

        Parameters:
          ws (WebSocket)           : The WebSocket connection to send to.
          payload (dict[str, Any]) : The JSON-serializable message to send.

        Returns:
          None
        """

        try :
            await ws.send_json(payload)
        except Exception:
            logger.exception("Failed to send WebSocket message")

manager = Manager()
