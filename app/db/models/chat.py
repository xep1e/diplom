# chat.py
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.db.database import Base

class ChatStatus(enum.Enum):
    new = "new"
    in_progress = "in_progress"
    closed = "closed"

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True, index=True)

    client_name = Column(String(100))
    client_external_id = Column(String(100))  # telegram_id

    status = Column(Enum(ChatStatus), default=ChatStatus.new)

    assigned_to = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)

    operator = relationship("User")