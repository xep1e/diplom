import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from alembic import context
from sqlalchemy import engine_from_config, pool
from logging.config import fileConfig

from app.db.models.user import User, UserRole
from app.db.models.task import Task
from app.db.models.message import Message
from app.db.models.chat import Chat
from app.db.models.rating import Rating
from app.db.models.client import Client
from app.db.models.chat_participant import ChatParticipant

from app.db.database import Base, DATABASE_URL

# Конфиг и логирование
config = context.config
fileConfig(config.config_file_name)
config.set_main_option('sqlalchemy.url', DATABASE_URL)

target_metadata = Base.metadata

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix='sqlalchemy.',
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

run_migrations_online()