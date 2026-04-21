from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models.chat import Chat, ChatStatus
from app.db.models.chat_participant import ChatParticipant, ParticipantRole
from app.db.models.user import User, UserRole
from app.api.userApi import get_current_user
from sqlalchemy import desc
from app.db.models.message import Message
from app.db.models.client import Client

router = APIRouter(prefix="/operator/chats", tags=["operator-chats"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/")
def get_my_chats(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.operator:
        raise HTTPException(status_code=403, detail="Operators only")

    # Находим все активные чаты оператора (не закрытые)
    links = db.query(ChatParticipant).join(Chat).filter(
        ChatParticipant.user_id == current_user.id,
        ChatParticipant.role == ParticipantRole.operator,
        Chat.status != ChatStatus.closed,
        Chat.is_active == True
    ).all()

    if not links:
        return []

    result = []
    for link in links:
        chat = db.query(Chat).filter(Chat.id == link.chat_id).first()

        last_msg = (
            db.query(Message)
            .filter(Message.chat_id == chat.id)
            .order_by(desc(Message.created_at))
            .first()
        )

        client_part = db.query(ChatParticipant).filter(
            ChatParticipant.chat_id == chat.id,
            ChatParticipant.client_id.isnot(None)
        ).first()

        client_name = None
        if client_part:
            client = db.query(Client).filter(Client.id == client_part.client_id).first()
            client_name = client.name if client else None

        result.append({
            "id": chat.id,
            "title": chat.title or client_name or f"Чат #{chat.id}",
            "status": chat.status.value,
            "last_message": last_msg.text[:50] + "..." if last_msg and len(last_msg.text) > 50 else (
                last_msg.text if last_msg else ""),
            "updated_at": (last_msg.created_at if last_msg else chat.created_at).isoformat() if (
                                                                                                            last_msg and last_msg.created_at) or chat.created_at else None
        })

    return result