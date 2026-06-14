from aiogram import Router, types
from app.db.database import SessionLocal
from app.bot.services_bot.addChatFromClientToBd import get_or_create_client, get_or_create_chat, save_message
from app.db.models.message import Message
from app.ws.chat_ws import manager
from app.redis_client import redis_manager
from app.db.models.chat import Chat, ChatStatus
from app.db.models.chat_participant import ChatParticipant
import uuid

router = Router()


@router.message()
async def handle_message(message: types.Message):
    db = SessionLocal()

    try:
        tg_user = message.from_user
        client = get_or_create_client(db, tg_user)

        # Проверяем, есть ли уже сообщения от клиента в этом чате
        # Находим или создаем чат (без отправки уведомления пока)

        # Сначала проверяем, есть ли активный чат у клиента
        active_participant = db.query(ChatParticipant).join(Chat).filter(
            ChatParticipant.client_id == client.id,
            Chat.status != ChatStatus.closed,
            Chat.is_active == True
        ).first()

        is_first_message = False

        if not active_participant:
            # Новый чат - первое сообщение
            is_first_message = True
            chat_id = get_or_create_chat(db, client)
        else:
            chat_id = active_participant.chat_id
            # Проверяем, есть ли уже сообщения от клиента в этом чате
            existing_messages = db.query(Message).filter(
                Message.chat_id == chat_id,
                Message.sender_client_id == client.id
            ).first()

            # Если нет ни одного сообщения от клиента - это первое
            is_first_message = (existing_messages is None)

            # Если чат в статусе waiting, переводим в new
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            if chat.status == ChatStatus.waiting:
                chat.status = ChatStatus.new
                db.commit()

        # Получаем чат для проверки статуса
        chat = db.query(Chat).filter(Chat.id == chat_id).first()

        # Обработка медиа (фото и т.д.)
        media_url = None
        media_type = None
        text = message.text or ""

        if message.photo:
            photo = message.photo[-1]
            file = await message.bot.get_file(photo.file_id)
            photo_data = await message.bot.download_file(file.file_path)
            photo_bytes = photo_data.read()

            photo_id = str(uuid.uuid4())
            cache_key = await redis_manager.save_photo(photo_bytes, photo_id)
            media_url = cache_key
            media_type = "image"
            text = message.caption or "📷 Фото"

        # Сохраняем сообщение
        msg = save_message(
            db,
            chat_id=chat_id,
            client_id=client.id,
            text=text,
            media_url=media_url,
            media_type=media_type
        )

        # Отправляем через WebSocket операторам
        await manager.broadcast(chat_id, {
            "id": msg.id,
            "text": text,
            "chat_id": chat_id,
            "sender": client.name,
            "sender_type": "client",
            "media_url": media_url,
            "media_type": media_type
        })

        # ✅ ОТПРАВЛЯЕМ ОТВЕТ КЛИЕНТУ ТОЛЬКО ДЛЯ ПЕРВОГО СООБЩЕНИЯ
        if is_first_message:
            await message.answer(
                "✅ *Сообщение получено!* Оператор ответит вам в ближайшее время.",
                parse_mode="Markdown"
            )
            print(f"📨 Отправлено приветственное сообщение клиенту {client.name} (первое сообщение)")
        else:
            # Для остальных сообщений - тишина
            print(f"🔇 Клиенту {client.name} не отправляем ответ (не первое сообщение)")

    except Exception as e:
        print(f"Ошибка в handle_message: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        db.close()