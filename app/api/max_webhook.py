from fastapi import APIRouter, Request
from app.db.database import SessionLocal

from app.bot.services_bot.addChatFromClientToBd import (
    get_or_create_chat,
    save_message
)

from app.db.models.client import (
    Client,
    ClientSource
)

from app.ws.chat_ws import manager

router = APIRouter()


@router.post("/max/webhook")
async def max_webhook(request: Request):

    db = SessionLocal()

    try:
        data = await request.json()

        print("MAX UPDATE:", data)

        # обрабатываем только сообщения
        if data.get("update_type") != "message_created":
            return {"ok": True}

        message = data["message"]

        sender = message["sender"]

        external_id = str(sender["user_id"])

        text = (
            message
            .get("body", {})
            .get("text", "")
        )

        client = (
            db.query(Client)
            .filter(
                Client.external_id == external_id,
                Client.source == ClientSource.max
            )
            .first()
        )

        if not client:

            name = (
                sender.get("first_name")
                or sender.get("name")
                or "MAX User"
            )

            client = Client(
                name=name,
                external_id=external_id,
                source=ClientSource.max
            )

            db.add(client)
            db.commit()
            db.refresh(client)

        chat_id = get_or_create_chat(
            db,
            client
        )

        msg = save_message(
            db=db,
            chat_id=chat_id,
            client_id=client.id,
            text=text
        )

        await manager.broadcast(
            chat_id,
            {
                "id": msg.id,
                "chat_id": chat_id,
                "text": msg.text,
                "sender": client.name,
                "sender_type": "client"
            }
        )

        print(
            f"✅ MAX сообщение сохранено chat={chat_id}"
        )

        return {"ok": True}

    except Exception as e:

        print("MAX ERROR:", e)

        return {
            "ok": False
        }

    finally:
        db.close()