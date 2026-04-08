from sqlalchemy import Column, Integer, ForeignKey

from app.db.database import Base

class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    id = Column(Integer, primary_key=True)

    chat_id = Column(Integer, ForeignKey("chats.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))