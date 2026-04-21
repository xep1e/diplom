from .bot import dp
from .handlers_bot.handlerBotAddChatToClient import router
from .handlers_bot.handlerBotRating import router as rating_router

def setup_bot():
    dp.include_router(router)
    dp.include_router(rating_router)