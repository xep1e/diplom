from sqlalchemy.orm import Session
from app.db.models.user import User, UserRole
from app.services.auth_service import hash_password


def create_user(db: Session, username: str, password: str, role: UserRole):
    hashed_password = hash_password(password)

    user = User(
        username=username,
        password_hash=hashed_password,
        role=role
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


def get_user(db: Session, user_id: int):
    return db.query(User).filter(User.id == user_id).first()


def get_users(db: Session):
    return db.query(User).all()


def update_user(db: Session, user_id: int, username: str = None, password: str = None):
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        return None

    if username:
        user.username = username

    if password:
        user.password_hash = hash_password(password)

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