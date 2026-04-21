from sqlalchemy.orm import Session
from app.db.models.client import Client, ClientSource
from app.db.models.chat import Chat, ChatStatus
from app.db.models.chat_participant import ChatParticipant, ParticipantRole
from app.db.models.message import Message
from datetime import datetime, timezone, timedelta

MSK = timezone(timedelta(hours=3))


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
    """Получить активный чат клиента или создать новый"""

    # Ищем активный чат (не закрытый)
    active_participant = db.query(ChatParticipant).join(Chat).filter(
        ChatParticipant.client_id == client.id,
        Chat.status != ChatStatus.closed,
        Chat.is_active == True
    ).first()

    if active_participant:
        # Возвращаем существующий активный чат
        chat = db.query(Chat).filter(Chat.id == active_participant.chat_id).first()
        if chat.status == ChatStatus.waiting:
            chat.status = ChatStatus.new
            db.commit()
        return active_participant.chat_id

    # Проверяем, были ли у клиента закрытые чаты
    closed_participants = db.query(ChatParticipant).join(Chat).filter(
        ChatParticipant.client_id == client.id,
        Chat.status == ChatStatus.closed
    ).order_by(Chat.created_at.desc()).all()

    if closed_participants:
        # Есть закрытые чаты - создаем новый чат как переоткрытие
        new_chat = Chat(
            title=client.name or "Клиент",
            status=ChatStatus.new,
            is_active=True,
            reopened_at=datetime.now(MSK)
        )
        db.add(new_chat)
        db.commit()
        db.refresh(new_chat)

        # Добавляем только клиента в новый чат (без оператора!)
        cp = ChatParticipant(
            chat_id=new_chat.id,
            client_id=client.id,
            role=ParticipantRole.client
        )
        db.add(cp)
        db.commit()

        # ❌ НЕ назначаем оператора автоматически

        print(f"🔄 Переоткрыт чат #{new_chat.id} для клиента {client.name} (без назначенного оператора)")
        return new_chat.id

    # Создаем новый чат (первое обращение) - тоже без оператора
    chat = Chat(
        title=client.name or "Клиент",
        status=ChatStatus.new,
        is_active=True
    )
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

    print(f"🆕 Новый чат #{chat.id} от клиента {client.name}")

    return chat.id


def save_message(db: Session, chat_id: int, client_id: int, text: str, media_url: str = None, media_type: str = None):
    """Сохранить сообщение"""
    msg = Message(
        chat_id=chat_id,
        sender_client_id=client_id,
        text=text,
        media_url=media_url,
        media_type=media_type
    )
    db.add(msg)
    db.commit()
    db.refresh(msg)

    return msg