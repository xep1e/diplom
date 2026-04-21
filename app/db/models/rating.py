from sqlalchemy import Column, Integer, ForeignKey, Boolean, DateTime
from datetime import datetime, timezone, timedelta

from app.db.database import Base

MSK = timezone(timedelta(hours=3))

def now_msk():
    return datetime.now(MSK)


class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id"))
    is_positive = Column(Boolean)
    created_at = Column(DateTime, default=now_msk)