from aiogram import Router, types
from app.db.database import SessionLocal
from ..services_bot.addChatFromClientToBd import get_or_create_client, get_or_create_chat, save_message
from app.ws.chat_ws import manager
router = Router()


@router.message()
async def handle_message(message: types.Message):
    db = SessionLocal()

    try:
        tg_user = message.from_user

        client = get_or_create_client(db, tg_user)
        chat_id = get_or_create_chat(db, client)

        msg = save_message(
            db,
            chat_id=chat_id,
            client_id=client.id,
            text=message.text or ""
        )

        # 🔥 ДОБАВЬ ВОТ ЭТО
        await manager.broadcast(chat_id, {
            "id": msg.id,
            "text": msg.text,
            "chat_id": chat_id,
            "sender": client.name
        })

        await message.answer("Сообщение получено 👍")

    finally:
        db.close()