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

        # Проверяем, был ли уже чат у клиента
        existing_chat = db.query(ChatParticipant).join(Chat).filter(
            ChatParticipant.client_id == client.id,
            Chat.status != ChatStatus.closed
        ).first()

        # Получаем или создаем чат
        chat_id = get_or_create_chat(db, client)

        # Определяем, новый ли чат
        is_new_chat = existing_chat is None

        # Получаем чат для проверки статуса
        chat = db.query(Chat).filter(Chat.id == chat_id).first()
        is_reopened = chat and chat.reopened_at is not None and chat.status == ChatStatus.new

        media_url = None
        media_type = None
        text = message.text or ""

        # Если есть фото
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

        # Отправляем ответ клиенту ТОЛЬКО для новых чатов или переоткрытых
        if is_new_chat or is_reopened:
            await message.answer(
                "✅ *Сообщение получено!* Оператор ответит вам в ближайшее время.",
                parse_mode="Markdown"
            )
        # Для существующих чатов - тишина, только если не было сообщения долгое время
        else:
            # Проверяем, когда было последнее сообщение от оператора
            last_operator_msg = db.query(Message).filter(
                Message.chat_id == chat_id,
                Message.sender_user_id.isnot(None)
            ).order_by(Message.created_at.desc()).first()

            # Если оператор не отвечал больше 5 минут, напомним
            if last_operator_msg:
                from datetime import datetime, timedelta
                time_since_last = datetime.utcnow() - last_operator_msg.created_at
                if time_since_last > timedelta(minutes=5):
                    await message.answer(
                        "⏳ *Сообщение доставлено!* Оператор скоро ответит.",
                        parse_mode="Markdown"
                    )
            # В остальных случаях - никакого ответа

    except Exception as e:
        print(f"Ошибка в handle_message: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        db.close()


@router.message(lambda message: message.text == "/start")
async def handle_start(message: types.Message):
    """Обработка команды /start"""
    db = SessionLocal()

    try:
        tg_user = message.from_user
        client = get_or_create_client(db, tg_user)

        # Проверяем, есть ли активный чат
        active_chat = db.query(ChatParticipant).join(Chat).filter(
            ChatParticipant.client_id == client.id,
            Chat.status != ChatStatus.closed,
            Chat.is_active == True
        ).first()

        if active_chat:
            chat = db.query(Chat).filter(Chat.id == active_chat.chat_id).first()

            # Проверяем, есть ли назначенный оператор
            operator_assigned = db.query(ChatParticipant).filter(
                ChatParticipant.chat_id == chat.id,
                ChatParticipant.role == ParticipantRole.operator
            ).first()

            if operator_assigned:
                await message.answer(
                    "💬 *У вас уже есть активный диалог!*\n\n"
                    f"Оператор {operator_assigned.user.username if hasattr(operator_assigned.user, 'username') else 'уже назначен'} скоро ответит.\n"
                    f"Если у вас новый вопрос, просто напишите его ниже.",
                    parse_mode="Markdown"
                )
            else:
                await message.answer(
                    "💬 *У вас уже есть активный диалог!*\n\n"
                    "Оператор будет назначен в ближайшее время.\n"
                    "Пожалуйста, ожидайте ответа.",
                    parse_mode="Markdown"
                )
        else:
            await message.answer(
                "🤖 *Здравствуйте!*\n\n"
                "Я бот технической поддержки.\n\n"
                "Опишите вашу проблему, и наш оператор свяжется с вами в ближайшее время.\n\n"
                "✏️ *Напишите ваше сообщение ниже:*",
                parse_mode="Markdown"
            )
    except Exception as e:
        print(f"Ошибка в /start: {e}")
        await message.answer("❌ Произошла ошибка. Попробуйте позже.")
    finally:
        db.close()