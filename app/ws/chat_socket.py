from fastapi import APIRouter
from fastapi import WebSocket
from fastapi import WebSocketDisconnect

from datetime import datetime
from datetime import timezone
from datetime import timedelta

from app.ws.chat_ws import manager
from app.ws.ws_auth import get_user_from_token

from app.db.database import SessionLocal

from app.db.models.message import Message
from app.db.models.chat import Chat
from app.db.models.chat import ChatStatus
from app.db.models.chat_participant import ChatParticipant
from app.db.models.client import Client
from app.db.models.client import ClientSource

from app.bot.bot import bot
from app.bot.max_sender import max_bot

router = APIRouter()

MSK = timezone(
    timedelta(hours=3)
)


@router.websocket("/ws/chat/{chat_id}")
async def chat_socket(
        websocket: WebSocket,
        chat_id: int
):

    token = websocket.query_params.get(
        "token"
    )

    user = get_user_from_token(
        token
    )

    if not user:

        await websocket.close(
            code=1008
        )

        return

    db = SessionLocal()

    await manager.connect(
        chat_id,
        websocket
    )

    try:

        while True:

            data = await websocket.receive_json()

            text = (
                data
                .get("text")
            )

            if not text:
                continue

            msg = Message(
                chat_id=chat_id,
                text=text,
                sender_user_id=user["user_id"]
            )

            db.add(msg)

            db.commit()

            db.refresh(msg)

            participant = (
                db.query(
                    ChatParticipant
                )
                .filter(
                    ChatParticipant.chat_id
                    == chat_id,

                    ChatParticipant.client_id
                    != None
                )
                .first()
            )

            if participant:

                client = (
                    db.query(Client)
                    .filter(
                        Client.id
                        ==
                        participant.client_id
                    )
                    .first()
                )

                if client:

                    try:

                        # TELEGRAM
                        if (
                                client.source
                                ==
                                ClientSource.telegram
                        ):

                            await bot.send_message(
                                chat_id=int(
                                    client.external_id
                                ),
                                text=(
                                    f"👨‍💻 "
                                    f"{user['username']}:\n\n"
                                    f"{text}"
                                )
                            )

                            print(
                                "✅ TG SENT"
                            )

                        # MAX
                        elif (
                                client.source
                                ==
                                ClientSource.max
                        ):

                            await (
                                max_bot
                                .send_message_to_user(
                                    user_id=int(
                                        client.external_id
                                    ),

                                    text=text,

                                    operator_name=(
                                        user[
                                            "username"
                                        ]
                                    )
                                )
                            )

                            print(
                                "✅ MAX SENT"
                            )

                    except Exception as e:

                        print(
                            "SEND ERROR:",
                            e
                        )

            await manager.broadcast(
                chat_id,
                {
                    "id": msg.id,

                    "text": msg.text,

                    "chat_id": chat_id,

                    "sender": (
                        user[
                            "username"
                        ]
                    ),

                    "sender_type": (
                        "operator"
                    )
                }
            )

    except WebSocketDisconnect:

        manager.disconnect(
            chat_id,
            websocket
        )

    finally:

        db.close()