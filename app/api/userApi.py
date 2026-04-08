from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.services.user_service import create_user, get_users, get_user, update_user, delete_user, verify_password
from app.db.database import SessionLocal
from app.db.models.user import UserRole, User
from pydantic import BaseModel
from passlib.hash import pbkdf2_sha256

router = APIRouter(tags=["Users"])

# Pydantic-модель для регистрации (роль не передаётся!)
class UserCreate(BaseModel):
    username: str
    password: str

# Dependency для сессии БД
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Регистрация оператора
@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    """
    Создаёт пользователя с ролью operator.
    """
    return create_user(db, username=user.username, password=user.password, role=UserRole.operator)


# Получить всех пользователей
@router.get("/")
def list_users(db: Session = Depends(get_db)):
    return get_users(db)


# Получить конкретного пользователя
@router.get("/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


# Обновить пользователя (только username и password)
@router.put("/{user_id}")
def edit_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    updated_user = update_user(db, user_id, username=user.username, password=user.password)
    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


# Удалить пользователя
@router.delete("/{user_id}")
def remove_user(user_id: int, db: Session = Depends(get_db)):
    success = delete_user(db, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"status": "deleted"}


class UserLogin(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()
    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    if db_user.role != UserRole.operator:
        raise HTTPException(status_code=403, detail="Доступ запрещён для этой роли")

    return {"id": db_user.id, "username": db_user.username, "role": db_user.role.value}