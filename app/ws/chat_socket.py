from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.chat_ws import manager
from app.db.database import SessionLocal
from app.db.models.message import Message
from app.ws.ws_auth import get_user_from_token

router = APIRouter()


@router.websocket("/ws/chat/{chat_id}")
async def chat_socket(websocket: WebSocket, chat_id: int):
    token = websocket.query_params.get("token")
    user = get_user_from_token(token)

    if not user:
        await websocket.close(code=1008)
        return

    db = SessionLocal()
    await manager.connect(chat_id, websocket)

    try:
        while True:
            data = await websocket.receive_json()

            msg = Message(
                chat_id=chat_id,
                text=data["text"],

                # 🔥 ВАЖНО: норм определение отправителя
                sender_user_id=user["user_id"] if user["role"] == "operator" else None,
                sender_client_id=None if user["role"] == "operator" else user["user_id"],
            )

            db.add(msg)
            db.commit()
            db.refresh(msg)

            await manager.broadcast(chat_id, {
                "id": msg.id,
                "text": msg.text,
                "chat_id": chat_id,
                "sender": user["username"]
            })

    except WebSocketDisconnect:
        manager.disconnect(chat_id, websocket)
    finally:
        db.close()