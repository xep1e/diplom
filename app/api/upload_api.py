from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session
from io import BytesIO
import uuid

from app.db.database import SessionLocal
from app.db.models.user import User, UserRole
from app.db.models.message import Message
from app.api.userApi import get_current_user
from app.redis_client import redis_manager
from app.ws.chat_ws import manager
from app.bot.bot import bot
from app.db.models.chat_participant import ChatParticipant
from app.db.models.client import Client

router = APIRouter(prefix="/upload", tags=["upload"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/photo")
async def upload_photo(
        file: UploadFile = File(...),
        chat_id: int = Form(...),
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Загрузка фото и отправка в Telegram"""

    print(f"📸 Получено фото от {current_user.username} для чата {chat_id}")

    if current_user.role not in [UserRole.operator, UserRole.admin]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    # Читаем файл
    photo_data = await file.read()

    # Генерируем уникальный ID
    photo_id = str(uuid.uuid4())

    # Сохраняем фото в Redis
    cache_key = await redis_manager.save_photo(photo_data, photo_id)

    print(f"📦 Фото сохранено в Redis с ключом: {cache_key}")

    # Сохраняем сообщение в БД
    msg = Message(
        chat_id=chat_id,
        text=file.filename or "📷 Фото",
        sender_user_id=current_user.id,
        media_url=cache_key,
        media_type="image"
    )

    db.add(msg)
    db.commit()
    db.refresh(msg)

    print(f"💾 Сообщение сохранено в БД: id={msg.id}, media_url={msg.media_url}")

    # Отправляем в Telegram
    client_part = db.query(ChatParticipant).filter(
        ChatParticipant.chat_id == chat_id,
        ChatParticipant.client_id != None
    ).first()

    # Вместо BytesIO, используем просто photo_data
    if client_part:
        client = db.query(Client).filter(Client.id == client_part.client_id).first()
        if client and client.external_id:
            try:
                # Отправляем файл напрямую
                from aiogram.types import FSInputFile
                import tempfile
                import os

                # Сохраняем временно
                with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                    tmp.write(photo_data)
                    tmp_path = tmp.name

                # Отправляем
                await bot.send_photo(
                    chat_id=client.external_id,
                    photo=FSInputFile(tmp_path),
                    caption=f"👨‍💻 {current_user.username}:\n{file.filename}"
                )

                # Удаляем временный файл
                os.unlink(tmp_path)

                print(f"✅ Фото отправлено в Telegram клиенту {client.external_id}")
            except Exception as e:
                print(f"❌ Ошибка отправки в Telegram: {e}")

    # Отправляем через WebSocket
    await manager.broadcast(chat_id, {
        "id": msg.id,
        "text": msg.text,
        "chat_id": chat_id,
        "sender": current_user.username,
        "sender_type": "operator",
        "media_url": cache_key,
        "media_type": "image"
    })

    print(f"✅ Готово! media_url={cache_key}")

    return {"status": "ok", "message_id": msg.id, "photo_key": cache_key}