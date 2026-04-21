from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime, timedelta
from typing import List, Dict, Any

from app.db.database import SessionLocal
from app.db.models.user import User, UserRole
from app.db.models.message import Message
from app.db.models.chat import Chat
from app.db.models.chat_participant import ChatParticipant, ParticipantRole
from app.api.userApi import get_current_user

router = APIRouter(prefix="/metrics", tags=["metrics"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/operators")
def get_operators_metrics(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Получить метрики всех операторов"""

    if current_user.role not in [UserRole.admin, UserRole.boss]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    # Получаем всех операторов
    operators = db.query(User).filter(User.role == UserRole.operator).all()

    result = []

    for operator in operators:
        # Находим все чаты оператора
        chat_links = db.query(ChatParticipant).filter(
            ChatParticipant.user_id == operator.id,
            ChatParticipant.role == ParticipantRole.operator
        ).all()

        chat_ids = [link.chat_id for link in chat_links]

        if not chat_ids:
            result.append({
                "id": operator.id,
                "username": operator.username,
                "total_chats": 0,
                "avg_response_time": None,
                "red_zone_count": 0,
                "red_zone_messages": [],
                "closed_chats": 0,
                "avg_resolution_time": None
            })
            continue

        # Получаем все сообщения оператора
        operator_messages = db.query(Message).filter(
            Message.chat_id.in_(chat_ids),
            Message.sender_user_id == operator.id
        ).order_by(Message.created_at).all()

        # Получаем все сообщения клиентов в этих чатах
        client_messages = db.query(Message).filter(
            Message.chat_id.in_(chat_ids),
            Message.sender_client_id.isnot(None)
        ).order_by(Message.created_at).all()

        # Словарь для быстрого поиска ответов
        response_times = []
        red_zone_messages = []

        # Анализируем время ответа на каждое сообщение клиента
        for client_msg in client_messages:
            # Ищем ответ оператора после этого сообщения
            operator_response = db.query(Message).filter(
                Message.chat_id == client_msg.chat_id,
                Message.sender_user_id == operator.id,
                Message.created_at > client_msg.created_at
            ).order_by(Message.created_at).first()

            if operator_response:
                response_time = (operator_response.created_at - client_msg.created_at).total_seconds()
                response_times.append(response_time)

                # Проверяем "красную зону" (больше 60 секунд для теста)
                if response_time > 60:  # 1 минута для теста, в продакшене 3600 (1 час)
                    red_zone_messages.append({
                        "chat_id": client_msg.chat_id,
                        "client_message": client_msg.text[:50],
                        "response_time_seconds": round(response_time),
                        "created_at": client_msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    })

        # Подсчитываем закрытые чаты за последние 7 дней
        week_ago = datetime.utcnow() - timedelta(days=7)
        closed_chats = db.query(Chat).filter(
            Chat.id.in_(chat_ids),
            Chat.status == "closed",
            Chat.closed_at >= week_ago
        ).count()

        # Среднее время решения (время от первого сообщения до закрытия чата)
        resolution_times = []
        for chat_id in chat_ids:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            first_msg = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at).first()
            if first_msg and chat.closed_at:
                resolution_time = (chat.closed_at - first_msg.created_at).total_seconds()
                resolution_times.append(resolution_time)

        avg_resolution_time = sum(resolution_times) / len(resolution_times) if resolution_times else None

        result.append({
            "id": operator.id,
            "username": operator.username,
            "total_chats": len(chat_ids),
            "avg_response_time": round(sum(response_times) / len(response_times)) if response_times else None,
            "red_zone_count": len(red_zone_messages),
            "red_zone_messages": red_zone_messages[:5],  # Показываем последние 5
            "closed_chats": closed_chats,
            "avg_resolution_time": round(avg_resolution_time / 60) if avg_resolution_time else None  # в минутах
        })

    return result


@router.get("/operators/{operator_id}/details")
def get_operator_details(
        operator_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Детальная статистика по оператору"""

    if current_user.role not in [UserRole.admin, UserRole.boss]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    operator = db.query(User).filter(User.id == operator_id).first()
    if not operator:
        raise HTTPException(status_code=404, detail="Оператор не найден")

    # Находим все чаты оператора
    chat_links = db.query(ChatParticipant).filter(
        ChatParticipant.user_id == operator.id,
        ChatParticipant.role == ParticipantRole.operator
    ).all()

    chat_ids = [link.chat_id for link in chat_links]

    # Получаем сообщения по дням
    last_7_days = []
    for i in range(7):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)

        messages_count = db.query(Message).filter(
            Message.chat_id.in_(chat_ids),
            Message.sender_user_id == operator.id,
            Message.created_at >= day_start,
            Message.created_at < day_end
        ).count()

        last_7_days.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "messages": messages_count
        })

    return {
        "id": operator.id,
        "username": operator.username,
        "last_7_days": last_7_days
    }