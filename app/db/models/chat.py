from sqlalchemy import Column, Integer, ForeignKey, Enum, DateTime, String, Boolean
from datetime import datetime, timezone, timedelta
import enum

from app.db.database import Base

# Московское время (UTC+3)
MSK = timezone(timedelta(hours=3))

def now_msk():
    return datetime.now(MSK)


class ChatStatus(enum.Enum):
    new = "new"
    in_progress = "in_progress"
    closed = "closed"
    waiting = "waiting"


class Chat(Base):
    __tablename__ = "chats"

    id = Column(Integer, primary_key=True)
    status = Column(Enum(ChatStatus), default=ChatStatus.new)
    title = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True)

    created_at = Column(DateTime, default=now_msk)
    closed_at = Column(DateTime, nullable=True)
    reopened_at = Column(DateTime, nullable=True)