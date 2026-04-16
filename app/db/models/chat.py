from sqlalchemy import Column, Integer, ForeignKey, Enum, DateTime,String
from datetime import datetime
import enum

from app.db.database import Base

class ChatStatus(enum.Enum):
    new = "new"
    in_progress = "in_progress"
    closed = "closed"

class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True)

    status = Column(Enum(ChatStatus), default=ChatStatus.new)
    title = Column(String(255), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)