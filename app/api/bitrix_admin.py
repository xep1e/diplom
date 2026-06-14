from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional
import requests
import os

from app.db.database import SessionLocal
from app.db.models.user import User, UserRole
from app.api.userApi import get_current_user

router = APIRouter(prefix="/bitrix", tags=["bitrix"])

# Твои вебхуки из .env
BITRIX_URL_GETUSERS = os.getenv("BITRIX_URL_GETUSERS", "https://b24-rej6pr.bitrix24.ru/rest/1/dgb4c3jc38h3ln1t/")
BITRIX_URL_CREATETASK = os.getenv("BITRIX_URL_CREATETASK", "https://b24-rej6pr.bitrix24.ru/rest/1/mxqqze6l5rygshpl/")
BITRIX_URL_GETTASKS = os.getenv("BITRIX_URL_GETTASKS",
                                "https://b24-rej6pr.bitrix24.ru/rest/1/mxqqze6l5rygshpl/")  # 👈 Добавили


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


class AssignBitrixIdRequest(BaseModel):
    user_id: int
    bitrix_user_id: int


class RemoveBitrixIdRequest(BaseModel):
    user_id: int


@router.get("/users")
def get_bitrix_users(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить список всех сотрудников из Bitrix24 (только для админа)"""

    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Доступ только администраторам")

    try:
        url = f"{BITRIX_URL_GETUSERS.rstrip('/')}/user.get"

        params = {
            "FILTER": {"ACTIVE": True},
            "SELECT": ["ID", "NAME", "LAST_NAME", "EMAIL", "PERSONAL_PHONE", "UF_DEPARTMENT"]
        }

        response = requests.post(url, json=params, timeout=30)
        result = response.json()

        print("Bitrix users response:", result)

        if "result" not in result:
            return {
                "ok": False,
                "error": result.get("error_description", "Ошибка Bitrix API"),
                "users": []
            }

        return {
            "ok": True,
            "users": result["result"],
            "total": len(result["result"])
        }

    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к Bitrix: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка подключения к Bitrix: {str(e)}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/assign-bitrix-id")
def assign_bitrix_id(
        data: AssignBitrixIdRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Назначить Bitrix ID оператору (только для админа)"""

    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Доступ только администраторам")

    target_user = db.query(User).filter(User.id == data.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    if target_user.role not in [UserRole.operator, UserRole.admin]:
        raise HTTPException(status_code=400, detail="Можно назначать Bitrix ID только операторам и администраторам")

    target_user.bitrix_user_id = data.bitrix_user_id

    try:
        check_url = f"{BITRIX_URL_GETUSERS.rstrip('/')}/user.get"
        check_response = requests.post(
            check_url,
            json={"FILTER": {"ID": data.bitrix_user_id}},
            timeout=10
        )
        check_result = check_response.json()

        if not check_result.get("result"):
            db.commit()
            return {
                "ok": True,
                "warning": f"Bitrix ID {data.bitrix_user_id} не найден в Bitrix24, но сохранен",
                "bitrix_user_id": data.bitrix_user_id
            }
    except:
        pass

    db.commit()

    return {
        "ok": True,
        "message": f"Bitrix ID {data.bitrix_user_id} назначен пользователю {target_user.username}",
        "user_id": target_user.id,
        "bitrix_user_id": target_user.bitrix_user_id
    }


@router.post("/remove-bitrix-id")
def remove_bitrix_id(
        data: RemoveBitrixIdRequest,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Отвязать Bitrix ID от оператора (только для админа)"""

    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Доступ только администраторам")

    target_user = db.query(User).filter(User.id == data.user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")

    target_user.bitrix_user_id = None
    db.commit()

    return {
        "ok": True,
        "message": f"Bitrix ID отвязан от пользователя {target_user.username}"
    }


@router.get("/users-site")
def get_site_users(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить список операторов сайта (только для админа)"""

    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Доступ только администраторам")

    users = db.query(User).filter(User.role.in_([UserRole.operator, UserRole.admin])).all()

    return {
        "ok": True,
        "users": [
            {
                "id": u.id,
                "username": u.username,
                "role": u.role.value,
                "bitrix_user_id": u.bitrix_user_id
            }
            for u in users
        ]
    }


@router.get("/my-tasks")
def get_my_tasks(
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Получить задачи текущего пользователя из Битрикс24 через task.item.list"""

    if not current_user.bitrix_user_id:
        raise HTTPException(status_code=400, detail="Bitrix ID не назначен. Обратитесь к администратору.")

    try:
        # Используем вебхук для получения задач
        webhook = BITRIX_URL_GETTASKS.rstrip('/')

        # 👇 Используем старый, но рабочий метод task.item.list
        url = f"{webhook}/task.item.list"

        # Параметры для task.item.list
        params = {
            "order": {"ID": "DESC"},  # Сортировка по ID (новые сверху)
            "filter": {
                "RESPONSIBLE_ID": current_user.bitrix_user_id  # Фильтр по исполнителю
            }
        }

        print(f"Запрашиваем задачи для Bitrix ID: {current_user.bitrix_user_id}")
        print(f"URL: {url}")
        print(f"Params: {params}")

        response = requests.post(url, json=params, timeout=30)
        result = response.json()

        print(f"Ответ Bitrix: {result}")

        # task.item.list возвращает result как массив
        if "result" not in result:
            return {
                "ok": False,
                "error": result.get("error_description", "Ошибка Bitrix API"),
                "tasks": []
            }

        # Преобразуем ответ в удобный формат
        tasks = []
        for task in result.get("result", []):
            tasks.append({
                "id": task.get("ID"),
                "title": task.get("TITLE"),
                "description": task.get("DESCRIPTION", ""),
                "status": str(task.get("STATUS", "1")),
                "status_label": get_status_label(str(task.get("STATUS", "1"))),
                "deadline": task.get("DEADLINE"),
                "created_date": task.get("CREATED_DATE"),
                "responsible_id": task.get("RESPONSIBLE_ID")
            })

        return {
            "ok": True,
            "tasks": tasks,
            "total": len(tasks)
        }

    except requests.exceptions.RequestException as e:
        print(f"Ошибка запроса к Bitrix: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка подключения к Bitrix: {str(e)}")
    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_status_label(status):
    """Преобразует статус задачи в человекочитаемый вид"""
    status_map = {
        "1": "Новая",
        "2": "Принята",
        "3": "Выполняется",
        "4": "Завершена",
        "5": "Отклонена",
        "6": "Отложена"
    }
    return status_map.get(str(status), f"Статус {status}")


@router.post("/update-task-status")
def update_task_status(
        task_id: int,
        status: str,
        current_user: User = Depends(get_current_user),
        db: Session = Depends(get_db)
):
    """Обновить статус задачи в Битрикс24"""

    if not current_user.bitrix_user_id:
        raise HTTPException(status_code=400, detail="Bitrix ID не назначен")

    # Проверяем, что статус валидный
    if status not in ["1", "2", "3", "4", "5", "6"]:
        raise HTTPException(status_code=400, detail="Неверный статус")

    try:
        webhook = BITRIX_URL_CREATETASK.rstrip('/')

        # Пробуем новый метод
        url = f"{webhook}/tasks.task.update"

        params = {
            "taskId": task_id,
            "fields": {"STATUS": status}
        }

        response = requests.post(url, json=params, timeout=30)
        result = response.json()

        # Если новый метод не работает, пробуем старый
        if "error" in result:
            url_old = f"{webhook}/task.item.update"
            params_old = {
                "id": task_id,
                "fields": {"STATUS": status}
            }
            response = requests.post(url_old, json=params_old, timeout=30)
            result = response.json()

        if "result" not in result:
            return {
                "ok": False,
                "error": result.get("error_description", "Ошибка обновления")
            }

        return {
            "ok": True,
            "message": "Статус обновлен"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))