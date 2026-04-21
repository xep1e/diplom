from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager

from app.api.userApi import router as user_router
from app.bot import setup_bot
from app.bot.bot import dp, bot
from app.api.upload_api import router as upload_router
from app.api.photo_api import router as photo_router
from app.redis_client import redis_manager
from app.api.metrics_api import router as metrics_router
from app.api.chat_actions_api import router as chat_actions_router

import asyncio
from app.api.chats_admin import router as admin_chats_router
from app.api.operator_chats import router as operator_chats_router
from app.ws.chat_socket import router as ws_router
from app.api.chat_api import router as chat_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🚀 старт
    await redis_manager.connect()
    setup_bot()
    task = asyncio.create_task(dp.start_polling(bot))

    yield

    # 🛑 остановка
    await redis_manager.disconnect()
    task.cancel()


app = FastAPI(
    title="ЛК Аналитика",
    lifespan=lifespan
)

# CORS - расширенная настройка
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# API
app.include_router(user_router, prefix="/api/users", tags=["users"])
app.include_router(admin_chats_router, prefix="", tags=["admin-chats"])
app.include_router(operator_chats_router, prefix="", tags=["operator-chats"])
app.include_router(ws_router)
app.include_router(chat_router)
app.include_router(upload_router, prefix="", tags=["upload"])
app.include_router(photo_router, prefix="", tags=["photo"])
app.include_router(metrics_router, prefix="", tags=["metrics"])
app.include_router(chat_actions_router, prefix="", tags=["chat-actions"])


@app.get("/")
def root():
    return {"message": "Backend работает!"}