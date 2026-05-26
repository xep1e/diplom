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
from app.db.models.rating import Rating
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
    """Получить метрики всех операторов с учетом рейтинга"""

    if current_user.role not in [UserRole.admin, UserRole.boss]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

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
                "avg_resolution_time": None,
                "likes": 0,
                "dislikes": 0,
                "rating_percent": 0,
                "kpi_score": 0
            })
            continue

        # Анализируем время ответа
        response_times = []
        red_zone_messages = []

        client_messages = db.query(Message).filter(
            Message.chat_id.in_(chat_ids),
            Message.sender_client_id.isnot(None)
        ).order_by(Message.created_at).all()

        for client_msg in client_messages:
            operator_response = db.query(Message).filter(
                Message.chat_id == client_msg.chat_id,
                Message.sender_user_id == operator.id,
                Message.created_at > client_msg.created_at
            ).order_by(Message.created_at).first()

            if operator_response:
                response_time = (operator_response.created_at - client_msg.created_at).total_seconds()
                response_times.append(response_time)

                if response_time > 60:  # Красная зона
                    red_zone_messages.append({
                        "chat_id": client_msg.chat_id,
                        "client_message": client_msg.text[:50],
                        "response_time_seconds": round(response_time),
                        "created_at": client_msg.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    })

        # Подсчитываем закрытые чаты
        week_ago = datetime.utcnow() - timedelta(days=7)
        closed_chats = db.query(Chat).filter(
            Chat.id.in_(chat_ids),
            Chat.status == "closed",
            Chat.closed_at >= week_ago
        ).count()

        # Получаем рейтинги по чатам оператора
        ratings = db.query(Rating).filter(Rating.chat_id.in_(chat_ids)).all()

        likes = sum(1 for r in ratings if r.is_positive)
        dislikes = sum(1 for r in ratings if not r.is_positive)
        total_ratings = likes + dislikes

        # Процент положительных оценок
        rating_percent = round((likes / total_ratings) * 100) if total_ratings > 0 else 0

        # Вычисляем KPI score (0-100)
        # Формула: 40% скорость ответа + 30% время решения + 30% рейтинг
        avg_response = sum(response_times) / len(response_times) if response_times else None
        avg_resolution = None

        # Время решения
        resolution_times = []
        for chat_id in chat_ids:
            chat = db.query(Chat).filter(Chat.id == chat_id).first()
            first_msg = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at).first()
            if first_msg and chat.closed_at:
                resolution_time = (chat.closed_at - first_msg.created_at).total_seconds()
                resolution_times.append(resolution_time)

        avg_resolution = sum(resolution_times) / len(resolution_times) if resolution_times else None

        # Нормируем показатели для KPI (0-100)
        # Скорость ответа: чем меньше секунд, тем лучше (норма 60 сек = 100 баллов)
        response_score = 100
        if avg_response:
            if avg_response <= 60:
                response_score = 100
            elif avg_response <= 300:
                response_score = 80 - ((avg_response - 60) / 240) * 30
            else:
                response_score = max(0, 50 - ((avg_response - 300) / 700) * 50)

        # Время решения: норма 30 минут = 100 баллов
        resolution_score = 100
        if avg_resolution:
            resolution_minutes = avg_resolution / 60
            if resolution_minutes <= 30:
                resolution_score = 100
            elif resolution_minutes <= 120:
                resolution_score = 80 - ((resolution_minutes - 30) / 90) * 30
            else:
                resolution_score = max(0, 50 - ((resolution_minutes - 120) / 480) * 50)

        # Рейтинг уже в процентах (0-100)
        rating_score = rating_percent

        # Итоговый KPI (веса можно настроить)
        kpi_score = round(
            response_score * 0.4 +  # 40% скорость ответа
            resolution_score * 0.3 +  # 30% время решения
            rating_score * 0.3  # 30% рейтинг
        )

        result.append({
            "id": operator.id,
            "username": operator.username,
            "total_chats": len(chat_ids),
            "avg_response_time": round(avg_response) if avg_response else None,
            "red_zone_count": len(red_zone_messages),
            "red_zone_messages": red_zone_messages[:5],
            "closed_chats": closed_chats,
            "avg_resolution_time": round(avg_resolution / 60) if avg_resolution else None,
            "likes": likes,
            "dislikes": dislikes,
            "rating_percent": rating_percent,
            "kpi_score": kpi_score,
            "response_score": round(response_score),
            "resolution_score": round(resolution_score),
            "rating_score": rating_score
        })

    # Сортируем по KPI score (от лучшего к худшему)
    result.sort(key=lambda x: x["kpi_score"], reverse=True)

    return result


@router.get("/operators/{operator_id}/details")
def get_operator_details(
        operator_id: int,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Детальная статистика по оператору с графиками"""

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

    # Получаем рейтинги по дням
    ratings_by_day = []
    for i in range(7):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)

        day_ratings = db.query(Rating).filter(
            Rating.chat_id.in_(chat_ids),
            Rating.created_at >= day_start,
            Rating.created_at < day_end
        ).all()

        likes = sum(1 for r in day_ratings if r.is_positive)
        dislikes = sum(1 for r in day_ratings if not r.is_positive)

        ratings_by_day.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "likes": likes,
            "dislikes": dislikes
        })

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

        # Среднее время ответа за день
        day_client_msgs = db.query(Message).filter(
            Message.chat_id.in_(chat_ids),
            Message.sender_client_id.isnot(None),
            Message.created_at >= day_start,
            Message.created_at < day_end
        ).all()

        day_response_times = []
        for client_msg in day_client_msgs:
            operator_response = db.query(Message).filter(
                Message.chat_id == client_msg.chat_id,
                Message.sender_user_id == operator.id,
                Message.created_at > client_msg.created_at,
                Message.created_at < day_end
            ).order_by(Message.created_at).first()

            if operator_response:
                response_time = (operator_response.created_at - client_msg.created_at).total_seconds()
                day_response_times.append(response_time)

        avg_response = sum(day_response_times) / len(day_response_times) if day_response_times else None

        last_7_days.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "messages": messages_count,
            "avg_response_time": round(avg_response) if avg_response else None
        })

    return {
        "id": operator.id,
        "username": operator.username,
        "last_7_days": last_7_days[::-1],  # Разворачиваем для хронологического порядка
        "ratings_by_day": ratings_by_day[::-1]
    }


@router.get("/rating-stats")
def get_rating_stats(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Общая статистика по рейтингам"""

    if current_user.role not in [UserRole.admin, UserRole.boss]:
        raise HTTPException(status_code=403, detail="Доступ запрещен")

    total_ratings = db.query(Rating).count()
    total_likes = db.query(Rating).filter(Rating.is_positive == True).count()
    total_dislikes = db.query(Rating).filter(Rating.is_positive == False).count()

    # Рейтинги по дням
    ratings_by_day = []
    for i in range(7):
        day = datetime.utcnow() - timedelta(days=i)
        day_start = datetime(day.year, day.month, day.day)
        day_end = day_start + timedelta(days=1)

        day_ratings = db.query(Rating).filter(
            Rating.created_at >= day_start,
            Rating.created_at < day_end
        ).all()

        ratings_by_day.append({
            "date": day_start.strftime("%Y-%m-%d"),
            "likes": sum(1 for r in day_ratings if r.is_positive),
            "dislikes": sum(1 for r in day_ratings if not r.is_positive)
        })

    return {
        "total_ratings": total_ratings,
        "total_likes": total_likes,
        "total_dislikes": total_dislikes,
        "average_rating": round((total_likes / total_ratings) * 100) if total_ratings > 0 else 0,
        "ratings_by_day": ratings_by_day[::-1]
    }