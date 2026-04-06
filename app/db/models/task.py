# task.py
from sqlalchemy import Column, Integer, String, ForeignKey

from app.db.database import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True)

    chat_id = Column(Integer, ForeignKey("chats.id"))
    bitrix_task_id = Column(String(100))
    title = Column(String(255))