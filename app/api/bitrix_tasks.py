from fastapi import APIRouter, UploadFile, Form, Depends, HTTPException
import requests
import json
import base64
from app.api.userApi import get_current_user
from app.db.models.user import User

router = APIRouter()

BITRIX_WEBHOOK = "https://b24-rej6pr.bitrix24.ru/rest/1/mxqqze6l5rygshpl"


@router.post("/create-task")
async def create_task(
        title: str = Form(...),
        description: str = Form(""),
        deadline: str = Form(None),
        checklist: str = Form("[]"),
        chat_id: int = Form(...),
        file: UploadFile = None,
        current_user: User = Depends(get_current_user)  # 👈 получаем текущего юзера
):
    try:
        # 👇 Проверяем, подключен ли Bitrix у пользователя
        if not current_user.bitrix_user_id:
            raise HTTPException(
                status_code=400,
                detail="Bitrix не подключен. Подключите Bitrix в профиле"
            )

        checks = json.loads(checklist)

        task_data = {
            "TITLE": title,
            "DESCRIPTION": f"""
{description}

Чат: #{chat_id}
Создал: {current_user.username}
            """,
            "RESPONSIBLE_ID": current_user.bitrix_user_id  # 👈 берем из БД
        }

        if deadline:
            task_data["DEADLINE"] = deadline

        # создаем задачу
        r = requests.post(
            f"{BITRIX_WEBHOOK}/task.item.add",
            json={"arNewTaskData": task_data}
        )

        result = r.json()
        print("Создание задачи:")
        print(result)

        if "result" not in result:
            return {
                "ok": False,
                "error": result
            }

        task_id = result["result"]
        print("Создана задача:", task_id)

        # ЧЕКЛИСТ
        for item in checks:
            if item.strip():
                checklist_response = requests.post(
                    f"{BITRIX_WEBHOOK}/task.checklistitem.add",
                    json={
                        "taskId": task_id,
                        "fields": {"TITLE": item}
                    }
                )
                print("Checklist:", checklist_response.text)

        # ФАЙЛ
        if file:
            print("Файл:", file.filename)
            content = await file.read()
            encoded = base64.b64encode(content).decode("utf-8")

            attach = requests.post(
                f"{BITRIX_WEBHOOK}/task.item.addfile",
                json={
                    "TASK_ID": task_id,
                    "FILE": {
                        "NAME": file.filename,
                        "CONTENT": encoded
                    }
                }
            )
            print("Ответ Bitrix:", attach.text)

        return {
            "ok": True,
            "task_id": task_id
        }

    except HTTPException:
        raise
    except Exception as e:
        print("Ошибка:", e)
        return {
            "ok": False,
            "error": str(e)
        }