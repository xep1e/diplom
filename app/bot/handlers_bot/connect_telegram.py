from aiogram import Router

from aiogram.types import Message

from datetime import datetime

from app.db.database import SessionLocal

from app.db.models.user import User

router = Router()


@router.message(
    lambda m:
    m.text
    and
    m.text.startswith(
        "/connect"
    )
)
async def connect(
        message: Message
):

    db = SessionLocal()

    try:

        parts = (
            message.text.split()
        )

        if len(parts) != 2:

            await message.answer(
                "Используйте:\n/connect TOKEN"
            )

            return

        token = parts[1]

        user = (
            db.query(User)
            .filter(
                User.telegram_connect_token
                ==
                token
            )
            .first()
        )

        if not user:

            await message.answer(
                "❌ Токен недействителен"
            )

            return

        user.telegram_chat_id = (
            str(
                message.chat.id
            )
        )

        user.telegram_connect_token = None

        user.telegram_connected_at = (
            datetime.utcnow()
        )

        db.commit()

        await message.answer(
            "✅ Telegram успешно подключён"
        )

    finally:

        db.close()