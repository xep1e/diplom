from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.api.userApi import router as user_router
from app.bot import setup_bot
from app.bot.bot import dp, bot

import asyncio
from app.api.chats_admin import router as admin_chats_router
from app.api.operator_chats import router as operator_chats_router
from app.ws.chat_socket import router as ws_router
from app.api.chat_api import router as chat_router





@asynccontextmanager
async def lifespan(app: FastAPI):
    # 🚀 старт
    setup_bot()
    task = asyncio.create_task(dp.start_polling(bot))

    yield

    # 🛑 остановка (опционально)
    task.cancel()


app = FastAPI(
    title="ЛК Аналитика",
    lifespan=lifespan
)


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API
app.include_router(user_router, prefix="/api/users", tags=["users"])
app.include_router(admin_chats_router, prefix="", tags=["admin-chats"])
app.include_router(operator_chats_router, prefix="", tags=["operator-chats"])
app.include_router(ws_router)
app.include_router(chat_router)

@app.get("/")
def root():
    return {"message": "Backend работает!"}