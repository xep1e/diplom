from sqlalchemy import Column, Integer, ForeignKey, Enum
import enum
from app.db.database import Base


class ParticipantRole(enum.Enum):
    client = "client"
    operator = "operator"


class ChatParticipant(Base):
    __tablename__ = "chat_participants"

    id = Column(Integer, primary_key=True)

    chat_id = Column(Integer, ForeignKey("chats.id"))

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)

    role = Column(Enum(ParticipantRole))