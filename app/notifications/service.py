from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.db.models.notification import Notification
from app.bot.bot import bot

MSK = timezone(timedelta(hours=3))


async def send_notification(
        db: Session,
        telegram_id: str,
        title: str,
        text: str,
        user_id: int = None
):
    try:

        msg = f"""
🚨 {title}

{text}
"""

        await bot.send_message(
            chat_id=telegram_id,
            text=msg
        )

        if user_id:
            n = Notification(
                user_id=user_id,
                title=title,
                text=text,
                is_sent=True,
                sent_at=datetime.now(MSK)
            )

            db.add(n)
            db.commit()

        return True

    except Exception as e:
        print(e)
        return False