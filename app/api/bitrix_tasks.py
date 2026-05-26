from fastapi import APIRouter, UploadFile, Form
import requests
import json
import base64

router = APIRouter()

BITRIX_WEBHOOK = "https://b24-rej6pr.bitrix24.ru/rest/1/mxqqze6l5rygshpl"

RESPONSIBLE_ID = 1


@router.post("/create-task")
async def create_task(
    title: str = Form(...),
    description: str = Form(""),
    deadline: str = Form(None),
    checklist: str = Form("[]"),
    chat_id: int = Form(...),
    file: UploadFile = None
):

    try:

        checks = json.loads(checklist)

        task_data = {

            "TITLE": title,

            "DESCRIPTION":
            f"""
{description}

Чат: #{chat_id}
            """,

            "RESPONSIBLE_ID":
            RESPONSIBLE_ID

        }

        if deadline:
            task_data["DEADLINE"] = deadline


        # создаем задачу
        r = requests.post(

            f"{BITRIX_WEBHOOK}/task.item.add",

            json={

                "arNewTaskData":
                task_data

            }

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


        # --------------------------
        # ЧЕКЛИСТ
        # --------------------------

        for item in checks:

            if item.strip():

                checklist_response = requests.post(

                    f"{BITRIX_WEBHOOK}/task.checklistitem.add",

                    json={

                        "taskId":
                        task_id,

                        "fields": {

                            "TITLE":
                            item

                        }

                    }

                )

                print(
                    "Checklist:",
                    checklist_response.text
                )


        # --------------------------
        # ФАЙЛ
        # --------------------------

        if file:

            print(
                "Файл:",
                file.filename
            )

            content = await file.read()

            encoded = base64.b64encode(
                content
            ).decode("utf-8")


            attach = requests.post(

                f"{BITRIX_WEBHOOK}/task.item.addfile",

                json={

                    "TASK_ID":
                    task_id,

                    "FILE": {

                        "NAME":
                        file.filename,

                        "CONTENT":
                        encoded

                    }

                }

            )


            print(
                "Ответ Bitrix:"
            )

            print(
                attach.text
            )


        return {

            "ok": True,

            "task_id": task_id

        }


    except Exception as e:

        print("Ошибка:")

        print(e)

        return {

            "ok": False,

            "error": str(e)

        }