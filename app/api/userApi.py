from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import SessionLocal
from app.db.models.user import UserRole, User
from app.services.user_service import create_user, get_user, get_users, update_user, delete_user
from app.services.auth_service import verify_password, create_access_token, SECRET_KEY
from pydantic import BaseModel
from fastapi.security import HTTPBearer
from jose import jwt

router = APIRouter()

security = HTTPBearer()


# ================= DB =================
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ================= SCHEMAS =================
class UserCreate(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


# ================= AUTH =================
def get_current_user(token=Depends(security), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token.credentials, SECRET_KEY, algorithms=["HS256"])
        user_id = int(payload.get("sub"))
    except:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    return user


# ================= ROUTES =================

@router.post("/register")
def register(user: UserCreate, db: Session = Depends(get_db)):
    return create_user(db, user.username, user.password, UserRole.operator)


@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == user.username).first()

    if not db_user or not verify_password(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    token = create_access_token({
        "sub": str(db_user.id),
        "username": db_user.username,
        "role": db_user.role.value
    })

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "username": current_user.username,
        "role": current_user.role.value
    }


@router.get("/")
def list_users(db: Session = Depends(get_db)):
    return get_users(db)


@router.get("/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    user = get_user(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.put("/{user_id}")
def edit_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    updated = update_user(db, user_id, user.username, user.password)

    if not updated:
        raise HTTPException(status_code=404, detail="User not found")

    return updated


@router.delete("/{user_id}")
def remove_user(user_id: int, db: Session = Depends(get_db)):
    success = delete_user(db, user_id)

    if not success:
        raise HTTPException(status_code=404, detail="User not found")

    return {"status": "deleted"}