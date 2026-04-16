from sqlalchemy.orm import Session
from app.db.models.client import Client, ClientSource
from app.db.models.chat import Chat
from app.db.models.chat_participant import ChatParticipant, ParticipantRole
from app.db.models.message import Message


def get_or_create_client(db: Session, tg_user):
    client = db.query(Client).filter_by(
        external_id=str(tg_user.id),
        source=ClientSource.telegram
    ).first()

    if not client:
        client = Client(
            name=tg_user.username or tg_user.full_name,
            external_id=str(tg_user.id),
            source=ClientSource.telegram
        )
        db.add(client)
        db.commit()
        db.refresh(client)

    return client


def get_or_create_chat(db: Session, client: Client):
    participant = db.query(ChatParticipant).filter_by(
        client_id=client.id
    ).first()

    if participant:
        return participant.chat_id

    # 👇 название чата = имя клиента
    chat = Chat(title=client.name or "Клиент")
    db.add(chat)
    db.commit()
    db.refresh(chat)

    cp = ChatParticipant(
        chat_id=chat.id,
        client_id=client.id,
        role=ParticipantRole.client
    )

    db.add(cp)
    db.commit()

    return chat.id

def save_message(db: Session, chat_id: int, client_id: int, text: str):
    msg = Message(
        chat_id=chat_id,
        sender_client_id=client_id,
        text=text
    )
    db.add(msg)
    db.commit()