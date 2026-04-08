from sqlalchemy.orm import Session
from app.db.models.user import User, UserRole
from passlib.hash import sha256_crypt

# app/services/user_service.py
import hashlib
from sqlalchemy.orm import Session
from app.db.models.user import User, UserRole

def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hashlib.sha256(password.encode("utf-8")).hexdigest() == hashed

def create_user(db: Session, username: str, password: str, role: UserRole = UserRole.operator):
    hashed_password = hash_password(password)
    user = User(username=username, password_hash=hashed_password, role=role)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_users(db: Session):
    return db.query(User).all()


def update_user(db: Session, user_id: int, username: str = None, password: str = None):
    """
    Изменение имени и пароля через API. Роль менять нельзя.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None

    if username:
        user.username = username
    if password:
        user.password_hash = sha256_crypt.hash(password)

    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return False
    db.delete(user)
    db.commit()
    return True