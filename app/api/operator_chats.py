from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models.chat import Chat
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

    links = db.query(ChatParticipant).filter(
        ChatParticipant.user_id == current_user.id,
        ChatParticipant.role == ParticipantRole.operator
    ).all()

    chat_ids = [l.chat_id for l in links]

    chats = db.query(Chat).filter(Chat.id.in_(chat_ids)).all()

    result = []

    for chat in chats:

        last_msg = (
            db.query(Message)
            .filter(Message.chat_id == chat.id)
            .order_by(desc(Message.created_at))
            .first()
        )

        # имя чата = либо title либо клиент
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
            "last_message": last_msg.text if last_msg else "",
            "updated_at": last_msg.created_at if last_msg else chat.created_at
        })

    return result