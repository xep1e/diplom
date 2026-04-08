from sqlalchemy import Column, Integer, ForeignKey, Text, DateTime, Boolean, String
from datetime import datetime

from app.db.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)

    chat_id = Column(Integer, ForeignKey("chats.id"))

    sender_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    sender_client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    text = Column(Text)

    media_url = Column(String(255), nullable=True)
    media_type = Column(String(20), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)