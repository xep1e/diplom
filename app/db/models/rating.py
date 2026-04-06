# rating.py
from sqlalchemy import Column, Integer, ForeignKey, Boolean

from app.db.database import Base

class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True)

    chat_id = Column(Integer, ForeignKey("chats.id"))
    is_positive = Column(Boolean)  # лайк / дизлайк