from .bot import dp
from .handlers_bot.handlerBotAddChatToClient import router

def setup_bot():
    dp.include_router(router)