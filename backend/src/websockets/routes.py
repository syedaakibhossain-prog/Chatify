import uuid
import json

from fastapi import (
    APIRouter,
    WebSocket,
    WebSocketDisconnect,
)

from src.database import SessionLocal

from src.websockets.manager import ConnectionManager
from src.websockets.schemas import WebSocketMessage
from src.websockets.service import WebSocketManager

from src.chat.MessageService import MessageService
from src.chat.MessageReposetory import MessageReposetory

from src.chat.ConversessionService import ConversessionService
from src.chat.ConversessionReposetory import ConversessionReposetory


router = APIRouter(
    prefix="/ws",
    tags=["WebSocket"],
)



# Dependencies


conversation_repo = ConversessionReposetory()
message_repo = MessageReposetory()

manager = ConnectionManager()

conversation_service = ConversessionService(
    conversation_repo
)

message_service = MessageService(
    message_repo,
    conversation_service,
)

websocket_service = WebSocketManager(
    manager,
    conversation_service,
    message_service,
)



# WebSocket


@router.websocket(
    "/conversession/{conversession_id}"
)
async def websocket_endpoint(
    websocket: WebSocket,
    conversession_id: uuid.UUID,
):

    print("[ROUTE] websocket endpoint reached")

    # Temporary user until we implement
    # WebSocket authentication
    user_id = uuid.UUID(
        "542956e5-0664-4398-8eb0-24110254fd20"
    )

    async with SessionLocal() as db:

        try:



            await websocket_service.connect_socket(
                db=db,
                websocket=websocket,
                conversession_id=conversession_id,
                user_id=user_id,
            )

            print("[ROUTE] websocket connected")



            while True:

                raw_message = (
                    await websocket.receive_text()
                )

                print(
                    f"[ROUTE] raw message: "
                    f"{raw_message!r}"
                )

                try:

                    # Parse JSON
                    data = json.loads(
                        raw_message
                    )

                    # Validate
                    message = (
                        WebSocketMessage
                        .model_validate(data)
                    )

                    print(
                        f"[ROUTE] validated: "
                        f"{message}"
                    )

                    # Handle message
                    await websocket_service.handel_message(
                        db=db,
                        conversession_id=conversession_id,
                        user_id=user_id,
                        message=message,
                    )

                except json.JSONDecodeError:

                    await websocket.send_json({
                        "type": "error",
                        "detail": "Invalid JSON",
                    })

                except Exception as e:

                    print(
                        "[ROUTE] message error:",
                        type(e).__name__,
                        str(e),
                    )

                    await websocket.send_json({
                        "type": "error",
                        "detail": str(e),
                    })

       

        except WebSocketDisconnect:

            print(
                "[ROUTE] websocket disconnected"
            )

            websocket_service.websocket_disconnect(
                conversession_id=conversession_id,
                websocket=websocket,
            )

        

        except Exception as e:

            print(
                "[ROUTE] unexpected error:",
                type(e).__name__,
                str(e),
            )

            websocket_service.websocket_disconnect(
                conversession_id=conversession_id,
                websocket=websocket,
            )