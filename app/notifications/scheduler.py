import asyncio

from app.db.database import SessionLocal

from app.notifications.rules import (
    get_users_with_failed_plan
)

from app.notifications.service import (
    send_notification
)


async def check_plan():

    while True:

        db = SessionLocal()

        try:

            failed = get_users_with_failed_plan(db)

            for item in failed:

                user = item["user"]

                if not user.bitrix_user_id:
                    continue

                await send_notification(
                    db=db,
                    telegram_id=user.bitrix_user_id,
                    user_id=user.id,
                    title="План не выполнен",
                    text=(
                        f"Вы выполнили "
                        f"{item['fact']} из {item['plan']}"
                    )
                )

        finally:
            db.close()

        await asyncio.sleep(3600)