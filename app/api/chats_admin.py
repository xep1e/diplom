from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.db.models.chat_participant import ChatParticipant
from app.db.models.client import Client
from app.db.database import SessionLocal
from app.db.models.chat import Chat
from app.db.models.user import User, UserRole
from app.db.models.chat_participant import ChatParticipant, ParticipantRole
from app.api.userApi import get_current_user
from app.bot.bot import bot

router = APIRouter(prefix="/admin/chats", tags=["admin-chats"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class RemoveRequest(BaseModel):
    chat_id: int
    username: str


class AssignRequest(BaseModel):
    chat_id: int
    username: str


@router.get("/")
def get_all_chats(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admins only")

    chats = db.query(Chat).all()

    result = []

    for chat in chats:
        participants = db.query(ChatParticipant).filter(
            ChatParticipant.chat_id == chat.id
        ).all()

        clients = []
        operators = []

        for p in participants:
            if p.client_id:
                client = db.query(Client).filter(Client.id == p.client_id).first()
                if client:
                    clients.append(client.name)

            if p.user_id:
                user = db.query(User).filter(User.id == p.user_id).first()
                if user:
                    operators.append(user.username)

        result.append({
            "id": chat.id,
            "title": chat.title,
            "status": chat.status.value,
            "clients": clients,
            "operators": operators
        })

    return result


@router.get("/operators")
def get_operators(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admins only")

    users = db.query(User).filter(User.role == UserRole.operator).all()

    return [
        {
            "id": u.id,
            "username": u.username
        }
        for u in users
    ]


@router.post("/assign")
async def assign_operator(
        data: AssignRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admins only")

    chat = db.query(Chat).filter(Chat.id == data.chat_id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    operator = db.query(User).filter(User.username == data.username).first()
    if not operator:
        raise HTTPException(status_code=404, detail="User not found")

    # Проверяем - уже назначен?
    exists = db.query(ChatParticipant).filter_by(
        chat_id=chat.id,
        user_id=operator.id
    ).first()

    if exists:
        return {"status": "already assigned"}

    cp = ChatParticipant(
        chat_id=chat.id,
        user_id=operator.id,
        role=ParticipantRole.operator
    )

    db.add(cp)
    db.commit()

    # Обновляем статус часа
    if chat.status == "new":
        chat.status = "in_progress"
        db.commit()

    # Отправляем уведомление клиенту в Telegram
    client_part = db.query(ChatParticipant).filter(
        ChatParticipant.chat_id == chat.id,
        ChatParticipant.client_id.isnot(None)
    ).first()

    if client_part:
        client = db.query(Client).filter(Client.id == client_part.client_id).first()
        if client and client.external_id:
            try:
                await bot.send_message(
                    chat_id=client.external_id,
                    text=f"👨‍💼 *Вам назначен оператор {operator.username}!*\n\n"
                         f"Специалист скоро ответит на ваше сообщение.\n"
                         f"Пожалуйста, ожидайте.",
                    parse_mode="Markdown"
                )
                print(f"✅ Уведомление отправлено клиенту {client.name} о назначении оператора {operator.username}")
            except Exception as e:
                print(f"❌ Ошибка отправки уведомления клиенту: {e}")

    return {"status": "assigned", "chat_id": chat.id, "operator": operator.username}


@router.post("/remove")
def remove_operator(
        data: RemoveRequest,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Admins only")

    operator = db.query(User).filter(User.username == data.username).first()
    if not operator:
        raise HTTPException(status_code=404, detail="User not found")

    participant = db.query(ChatParticipant).filter_by(
        chat_id=data.chat_id,
        user_id=operator.id
    ).first()

    if not participant:
        raise HTTPException(status_code=404, detail="Operator not in chat")

    db.delete(participant)
    db.commit()

    return {"status": "removed", "chat_id": data.chat_id, "operator": data.username}