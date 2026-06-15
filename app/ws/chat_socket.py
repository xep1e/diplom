from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.ws.chat_ws import manager
from app.db.database import SessionLocal
from app.db.models.message import Message
from app.db.models.chat import Chat, ChatStatus
from app.ws.ws_auth import get_user_from_token
from app.bot.bot import bot
from app.db.models.chat_participant import ChatParticipant
from app.db.models.client import Client, ClientSource  # 👈 ДОБАВИТЬ ClientSource
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
                        # 👇 ОТПРАВКА В TELEGRAM (существующий код)
                        await bot.send_message(
                            chat_id=client.external_id,
                            text=f"👨‍💻 {user['username']}:\n{data['text']}"
                        )

                        # 👇👇👇 НОВЫЙ БЛОК ДЛЯ MAX 👇👇👇
                        # Отправляем в MAX, если клиент из MAX
                        if client.source == ClientSource.max:
                            from app.bot.max_bot import max_bot
                            if max_bot:
                                try:
                                    await max_bot.send_message_to_user(
                                        user_id=int(client.external_id),  # external_id содержит user_id из MAX
                                        text=data['text'],
                                        operator_name=user['username']
                                    )
                                    print(f"✅ Сообщение отправлено в MAX пользователю {client.external_id}")
                                except Exception as e:
                                    print(f"❌ Ошибка отправки в MAX: {e}")
                        # 👆👆👆 КОНЕЦ БЛОКА ДЛЯ MAX 👆👆👆

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
                            # Отправляем запрос на оценку в Telegram
                            await send_rating_request(chat_id, client.external_id, bot)

                            # 👇👇👇 ДЛЯ MAX ТОЖЕ МОЖНО ОТПРАВИТЬ ЗАПРОС НА ОЦЕНКУ 👇👇👇
                            if client.source == ClientSource.max:
                                from app.bot.max_bot import max_bot
                                if max_bot:
                                    # Отправляем клавиатуру с оценкой в MAX
                                    keyboard = {
                                        "inline_keyboard": [
                                            [
                                                {"text": "👍 Хорошо", "callback_data": f"rate_like_{chat_id}"},
                                                {"text": "👎 Плохо", "callback_data": f"rate_dislike_{chat_id}"}
                                            ]
                                        ]
                                    }
                                    await max_bot.send_message_to_user(
                                        user_id=int(client.external_id),
                                        text="💬 Диалог завершен.\n\nОцените, пожалуйста, качество обслуживания:",
                                        keyboard=keyboard
                                    )

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