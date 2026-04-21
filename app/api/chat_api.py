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
        sender_type = None

        if m.sender_user_id is not None:
            user = db.query(User).filter(User.id == m.sender_user_id).first()
            if user:
                sender = user.username
                sender_type = "operator"
        elif m.sender_client_id is not None:
            client = db.query(Client).filter(Client.id == m.sender_client_id).first()
            if client:
                sender = client.name
                sender_type = "client"
        else:
            continue

        result.append({
            "id": m.id,
            "text": m.text,
            "sender": sender,
            "sender_type": sender_type,
            "media_url": m.media_url,  # Это будет ключ кэша Redis
            "media_type": m.media_type
        })

    return result