from aiogram import Router, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models.rating import Rating
from app.db.models.chat import Chat, ChatStatus
from app.db.models.chat_participant import ChatParticipant
from app.db.models.client import Client

router = Router()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.callback_query(lambda c: c.data.startswith('rate_'))
async def handle_rating(callback_query: types.CallbackQuery):
    """Обработка оценки от клиента"""

    # rate_like_123 или rate_dislike_123
    parts = callback_query.data.split('_')
    rating_type = parts[1]  # like или dislike
    chat_id = int(parts[2])

    db = next(get_db())

    try:
        # Проверяем, есть ли уже оценка
        existing_rating = db.query(Rating).filter(Rating.chat_id == chat_id).first()

        if existing_rating:
            await callback_query.message.edit_text(
                "🙏 Спасибо! Вы уже оценили наш диалог."
            )
            await callback_query.answer()
            return

        # Сохраняем оценку
        is_positive = (rating_type == 'like')
        rating = Rating(
            chat_id=chat_id,
            is_positive=is_positive
        )

        db.add(rating)
        db.commit()

        # Отправляем сообщение
        if is_positive:
            await callback_query.message.edit_text(
                "❤️ Спасибо за положительную оценку! Мы рады, что смогли помочь.\n\n"
                "Если у вас будут вопросы - обращайтесь!"
            )
        else:
            await callback_query.message.edit_text(
                "😔 Спасибо за честную обратную связь. Мы работаем над улучшением качества обслуживания.\n\n"
                "Если у вас есть предложения, напишите нам!"
            )

        await callback_query.answer()

    finally:
        db.close()


async def send_rating_request(chat_id: int, client_external_id: str, bot):
    """Отправить запрос на оценку клиенту"""

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍 Хорошо", callback_data=f"rate_like_{chat_id}"),
            InlineKeyboardButton(text="👎 Плохо", callback_data=f"rate_dislike_{chat_id}")
        ]
    ])

    await bot.send_message(
        chat_id=client_external_id,
        text="💬 Диалог завершен.\n\n"
             "Оцените, пожалуйста, качество обслуживания:",
        reply_markup=keyboard
    )