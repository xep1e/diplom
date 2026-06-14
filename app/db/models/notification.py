from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, DateTime
from datetime import datetime, timezone, timedelta

from app.db.database import Base

MSK = timezone(timedelta(hours=3))


def now_msk():
    return datetime.now(MSK)


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True)

    user_id = Column(Integer, ForeignKey("users.id"))

    title = Column(String(255))
    text = Column(String(2000))

    is_sent = Column(Boolean, default=False)

    created_at = Column(DateTime, default=now_msk)
    sent_at = Column(DateTime, nullable=True)