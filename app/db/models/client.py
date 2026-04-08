from sqlalchemy import Column, Integer, String, DateTime, Enum
from datetime import datetime
import enum

from app.db.database import Base

class ClientSource(enum.Enum):
    telegram = "telegram"
    max = "max"

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True)
    name = Column(String(100))

    external_id = Column(String(100), index=True)
    source = Column(Enum(ClientSource))

    created_at = Column(DateTime, default=datetime.utcnow)