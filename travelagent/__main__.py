import logging

from aiogram import types
from aiogram_dialog import setup_dialogs
from tortoise import Tortoise, connections

from . import monkeypatch  # noqa
from .config import TORTOISE_ORM
from .dialogs import dialogs
from .middlewares import ACLMiddleware, DatabaseI18nMiddleware
from .misc import bot, dp, i18n

logging.basicConfig(
    level=logging.INFO,
    format="[%(levelname)s] %(asctime)s - %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


@dp.startup()
async def on_startup():
    await bot.delete_webhook(drop_pending_updates=True)

    dp.update.middleware(ACLMiddleware())
    dp.update.middleware(DatabaseI18nMiddleware(i18n))

    dp.include_routers(*dialogs)
    setup_dialogs(dp)

    await Tortoise.init(TORTOISE_ORM)

    await bot.set_my_commands(
        [
            types.BotCommand(command="start", description="Запустить бота"),
            types.BotCommand(
                command="show", description="Показать текущий экран"
            ),
        ],
        scope=types.BotCommandScopeAllPrivateChats(),
    )


@dp.shutdown()
async def on_shutdown():
    await connections.close_all()


if __name__ == "__main__":
    dp.run_polling(bot, allowed_updates=["message", "callback_query"])
