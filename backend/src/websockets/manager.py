from fastapi import WebSocket


class ConnectionManager:

    def __init__(self):

        self.active_connections : dict[
            str , set[WebSocket]
        ] ={}

    async def connect(
        self,
        conversession_id: str,
        websocket: WebSocket
    ) -> None:

        await websocket.accept()
        print("websocket connected")

        if conversession_id not in self.active_connections:
            self.active_connections[conversession_id] = set()
        
        self.active_connections[conversession_id].add(websocket)

    def diconnect(
        self,
        conversession_id: str,
        websocket: WebSocket
    ) -> None:

        connections = self.active_connections.get(
            conversession_id
        )

        if not connections:
            return
        
        connections.discard(websocket)
        print("websocket disconnected")

    async def broadcast(
        self,
        conversession_id: str,
        message: dict
    ) -> None:

        connections = self.active_connections.get(
            conversession_id,
            set(),
        )

        for websocket in connections:
            await websocket.send_json(message)