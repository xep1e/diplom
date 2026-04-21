from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.chat_ws import manager
from app.db.database import SessionLocal
from app.db.models.message import Message
from app.db.models.chat import Chat, ChatStatus
from app.ws.ws_auth import get_user_from_token
from app.bot.bot import bot
from app.db.models.chat_participant import ChatParticipant
from app.db.models.client import Client
from app.bot.handlers_bot.handlerBotRating import send_rating_request
from datetime import datetime
from datetime import datetime, timezone, timedelta



router = APIRouter()
MSK = timezone(timedelta(hours=3))

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

            # Текстовые сообщения
            if "text" in data and data["text"]:
                msg = Message(
                    chat_id=chat_id,
                    text=data["text"],
                    sender_user_id=user["user_id"],
                    sender_client_id=None
                )

                db.add(msg)
                db.commit()
                db.refresh(msg)

                # Отправляем в Telegram
                client_part = db.query(ChatParticipant).filter(
                    ChatParticipant.chat_id == chat_id,
                    ChatParticipant.client_id != None
                ).first()

                if client_part:
                    client = db.query(Client).filter(Client.id == client_part.client_id).first()
                    if client and client.external_id:
                        await bot.send_message(
                            chat_id=client.external_id,
                            text=f"👨‍💻 {user['username']}:\n{data['text']}"
                        )

                await manager.broadcast(chat_id, {
                    "id": msg.id,
                    "text": msg.text,
                    "chat_id": chat_id,
                    "sender": user["username"],
                    "sender_type": "operator",
                    "type": "message"
                })

            # Закрытие чата
            elif "action" in data and data["action"] == "close_chat":
                chat = db.query(Chat).filter(Chat.id == chat_id).first()
                if chat and chat.status != ChatStatus.closed:
                    chat.status = ChatStatus.closed
                    chat.closed_at = datetime.now(MSK)
                    db.commit()

                    # Получаем клиента для отправки запроса оценки
                    client_part = db.query(ChatParticipant).filter(
                        ChatParticipant.chat_id == chat_id,
                        ChatParticipant.client_id != None
                    ).first()

                    if client_part:
                        client = db.query(Client).filter(Client.id == client_part.client_id).first()
                        if client and client.external_id:
                            # Отправляем запрос на оценку
                            await send_rating_request(chat_id, client.external_id, bot)

                    await manager.broadcast(chat_id, {
                        "type": "chat_closed",
                        "chat_id": chat_id,
                        "closed_by": user["username"],
                        "closed_at": chat.closed_at.isoformat()
                    })

    except WebSocketDisconnect:
        manager.disconnect(chat_id, websocket)
    finally:
        db.close()