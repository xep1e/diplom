# app/db/models/user.py
from sqlalchemy import Column, Integer, String, Enum, Boolean
from app.db.database import Base
import enum

class UserRole(enum.Enum):
    operator = "operator"
    admin = "admin"
    boss = "boss"

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

    role = Column(Enum(UserRole), default=UserRole.operator)
    is_active = Column(Boolean, default=True)