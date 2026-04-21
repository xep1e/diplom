from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta

from app.db.database import SessionLocal
from app.db.models.chat import Chat, ChatStatus
from app.db.models.chat_participant import ChatParticipant, ParticipantRole
from app.db.models.user import User, UserRole
from app.db.models.rating import Rating
from app.db.models.client import Client
from app.api.userApi import get_current_user
from app.ws.chat_ws import manager
from app.bot.bot import bot

router = APIRouter(prefix="/chat", tags=["chat-actions"])

MSK = timezone(timedelta(hours=3))
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/{chat_id}/close")
def close_chat(
        chat_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Закрыть диалог"""

    if current_user.role not in [UserRole.operator, UserRole.admin]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    chat = db.query(Chat).filter(Chat.id == chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Чат не найден")

    if chat.status == ChatStatus.closed:
        return {"status": "already_closed", "message": "Чат уже закрыт"}

    # Закрываем чат
    chat.status = ChatStatus.closed
    chat.closed_at = datetime.now(MSK)
    chat.is_active = False

    db.commit()

    # Отправляем уведомление через WebSocket
    import asyncio
    asyncio.create_task(manager.broadcast(chat_id, {
        "type": "chat_closed",
        "chat_id": chat_id,
        "closed_by": current_user.username,
        "closed_at": chat.closed_at.isoformat()
    }))

    return {
        "status": "closed",
        "chat_id": chat_id,
        "closed_by": current_user.username,
        "closed_at": chat.closed_at
    }


@router.post("/reopen")
def reopen_chat(
        client_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Переоткрыть чат (только для админа или при повторном обращении клиента)"""

    # Находим последний чат клиента
    last_chat_participant = db.query(ChatParticipant).filter(
        ChatParticipant.client_id == client_id
    ).order_by(ChatParticipant.id.desc()).first()

    if not last_chat_participant:
        raise HTTPException(status_code=404, detail="Чаты не найдены")

    last_chat = db.query(Chat).filter(Chat.id == last_chat_participant.chat_id).first()

    # Если чат уже открыт
    if last_chat.status != ChatStatus.closed:
        return {
            "status": "already_open",
            "chat_id": last_chat.id,
            "message": "Чат уже открыт"
        }

    # Создаем новый чат
    new_chat = Chat(
        title=last_chat.title,
        status=ChatStatus.new,
        is_active=True,
        reopened_at=datetime.utcnow()
    )

    db.add(new_chat)
    db.commit()
    db.refresh(new_chat)

    # Добавляем клиента в новый чат
    cp = ChatParticipant(
        chat_id=new_chat.id,
        client_id=client_id,
        role=ParticipantRole.client
    )
    db.add(cp)
    db.commit()

    # Если есть оператор, который вел предыдущий чат, можно его назначить
    old_operator = db.query(ChatParticipant).filter(
        ChatParticipant.chat_id == last_chat.id,
        ChatParticipant.role == ParticipantRole.operator
    ).first()

    if old_operator:
        new_cp = ChatParticipant(
            chat_id=new_chat.id,
            user_id=old_operator.user_id,
            role=ParticipantRole.operator
        )
        db.add(new_cp)
        db.commit()

    return {
        "status": "reopened",
        "chat_id": new_chat.id,
        "message": "Создан новый чат"
    }


@router.get("/client/{client_id}/last")
def get_client_last_chat(
        client_id: int,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить последний чат клиента"""

    if current_user.role not in [UserRole.operator, UserRole.admin]:
        raise HTTPException(status_code=403, detail="Недостаточно прав")

    last_participant = db.query(ChatParticipant).filter(
        ChatParticipant.client_id == client_id
    ).order_by(ChatParticipant.id.desc()).first()

    if not last_participant:
        return {"has_chat": False}

    chat = db.query(Chat).filter(Chat.id == last_participant.chat_id).first()

    return {
        "has_chat": True,
        "chat_id": chat.id,
        "status": chat.status.value,
        "created_at": chat.created_at,
        "closed_at": chat.closed_at
    }