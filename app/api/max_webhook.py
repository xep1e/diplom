from fastapi import APIRouter, HTTPException, Request
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models.client import Client, ClientSource
from app.db.models.chat import Chat, ChatStatus
from app.db.models.chat_participant import ChatParticipant, ParticipantRole
from app.db.models.message import Message
import logging

router = APIRouter(prefix="/max", tags=["max-webhook"])
logger = logging.getLogger(__name__)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/webhook")
async def max_webhook(request: Request):
    """ПРОСТОЙ вебхук для получения сообщений от MAX - только сохранение в БД"""
    try:
        data = await request.json()

        # Логируем для отладки
        logger.info(f"📨 Получен вебхук от MAX: {data}")
        print(f"📨 Получен вебхук от MAX: {data}")

        # Быстро возвращаем OK, чтобы MAX не пересылал повторно
        # А обработку делаем синхронно для простоты

        db = next(get_db())

        try:
            # Определяем тип события
            event_type = data.get("type")

            if event_type == "message_created":
                message_data = data.get("message", {})
                sender = message_data.get("sender", {})
                chat = message_data.get("chat", {})

                max_user_id = sender.get("user_id")
                max_chat_id = chat.get("chat_id")

                if not max_user_id:
                    print(f"⚠️ Нет user_id в сообщении")
                    return {"status": "ok"}

                # Получаем или создаем клиента
                client = db.query(Client).filter(
                    Client.external_id == str(max_user_id),
                    Client.source == ClientSource.max
                ).first()

                if not client:
                    client = Client(
                        name=sender.get("name", f"MAX User {max_user_id}"),
                        external_id=str(max_user_id),
                        source=ClientSource.max
                    )
                    db.add(client)
                    db.commit()
                    db.refresh(client)
                    print(f"✅ Создан новый клиент MAX: {client.name} (id: {client.id})")
                else:
                    print(f"✅ Найден существующий клиент MAX: {client.name} (id: {client.id})")

                # Находим или создаем чат
                # Ищем активный чат клиента
                active_participant = db.query(ChatParticipant).join(Chat).filter(
                    ChatParticipant.client_id == client.id,
                    Chat.status != ChatStatus.closed,
                    Chat.is_active == True
                ).first()

                if active_participant:
                    system_chat = db.query(Chat).filter(Chat.id == active_participant.chat_id).first()
                    print(f"📌 Найден активный чат #{system_chat.id} для клиента {client.name}")
                else:
                    # Создаем новый чат
                    system_chat = Chat(
                        title=client.name or "Клиент MAX",
                        status=ChatStatus.new,
                        is_active=True
                    )
                    db.add(system_chat)
                    db.commit()
                    db.refresh(system_chat)

                    # Добавляем клиента в чат
                    cp = ChatParticipant(
                        chat_id=system_chat.id,
                        client_id=client.id,
                        role=ParticipantRole.client
                    )
                    db.add(cp)
                    db.commit()

                    print(f"🆕 Создан новый чат #{system_chat.id} для клиента MAX {client.name}")

                # Сохраняем текст сообщения
                text = message_data.get("text", "")

                # Обработка вложений (упрощенно)
                attachments = message_data.get("attachments", [])
                media_url = None
                media_type = None

                for att in attachments:
                    if att.get("type") == "image":
                        media_url = att.get("url")
                        media_type = "image"
                        text = text or "📷 Фото"
                    elif att.get("type") == "file":
                        media_url = att.get("url")
                        media_type = "file"
                        text = text or "📎 Файл"

                # Сохраняем сообщение в БД
                msg = Message(
                    chat_id=system_chat.id,
                    text=text,
                    sender_client_id=client.id,
                    media_url=media_url,
                    media_type=media_type
                )
                db.add(msg)
                db.commit()
                db.refresh(msg)

                print(f"💾 Сохранено сообщение #{msg.id} от {client.name} в чат #{system_chat.id}: {text[:50]}")

            else:
                print(f"ℹ️ Получено событие типа: {event_type}")

        except Exception as e:
            print(f"❌ Ошибка при обработке сообщения MAX: {e}")
            import traceback
            traceback.print_exc()
        finally:
            db.close()

        return {"status": "ok"}

    except Exception as e:
        print(f"❌ Ошибка в вебхуке MAX: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/test")
async def test_max():
        """Тестовый эндпоинт для проверки"""
        return {
            "status": "ok",
            "message": "MAX webhook endpoint is ready",
            "webhook_url": "/max/webhook"
        }