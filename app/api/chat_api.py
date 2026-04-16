from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import SessionLocal
from app.db.models.message import Message
from app.db.models.user import User
from app.db.models.client import Client

router = APIRouter(prefix="/chats", tags=["chats"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/{chat_id}/messages")
def get_messages(chat_id: int, db: Session = Depends(get_db)):
    msgs = db.query(Message).filter(
        Message.chat_id == chat_id
    ).order_by(Message.created_at).all()

    result = []

    for m in msgs:
        sender = None

        if m.sender_user_id:
            user = db.query(User).filter(User.id == m.sender_user_id).first()
            sender = user.username if user else "unknown"

        elif m.sender_client_id:
            client = db.query(Client).filter(Client.id == m.sender_client_id).first()
            sender = client.name if client else "client"

        result.append({
            "id": m.id,
            "text": m.text,
            "sender": sender
        })

    return result