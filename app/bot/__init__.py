from .bot import dp

from .handlers_bot.connect_telegram import (
    router as connect_router
)

from .handlers_bot.handlerBotRating import (
    router as rating_router
)

from .handlers_bot.handlerBotAddChatToClient import (
    router as chat_router
)


def setup_bot():

    # сначала команды
    dp.include_router(
        connect_router
    )

    # потом callback
    dp.include_router(
        rating_router
    )

    # самым последним общий чат
    dp.include_router(
        chat_router
    )