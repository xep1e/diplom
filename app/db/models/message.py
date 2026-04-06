# message.py
from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, Boolean
from datetime import datetime
from app.db.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)

    chat_id = Column(Integer, ForeignKey("chats.id"))
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    text = Column(Text)

    is_from_client = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)