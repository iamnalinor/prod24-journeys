import os
import unittest
from pathlib import Path

from aiogram import types
from babel.support import LazyProxy
from tortoise import Tortoise

os.chdir(Path(__file__).parent.parent)

from travelagent.models import Journey, User  # noqa
from travelagent.services.journey import JourneyUtils  # noqa
from travelagent.misc import i18n  # noqa


class DummyBot:
    def __init__(self):
        self.calls = []

    async def send_message(
        self,
        chat_id: int,
        text: str,
        reply_markup: types.ReplyKeyboardMarkup = None,
    ):
        self.calls.append((chat_id, text, reply_markup))


def dummy_gettext(text: str) -> str:
    return f"{text} {i18n.current_locale}"


class JourneyTestCase(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        await Tortoise.init(
            db_url="sqlite://:memory:",
            modules={"models": ["travelagent.models"]},
        )
        await Tortoise.generate_schemas()

        self.users = [
            await User.create(id=10, lang_code="eo"),
            await User.create(id=20, lang_code="en"),
            await User.create(id=30, lang_code="es"),
        ]
        self.journey = await Journey.create(name="Test")
        await self.journey.users.add(*self.users)

        self.utils = JourneyUtils(self.journey)

    async def asyncTearDown(self):
        await Tortoise.close_connections()

    async def test_has_kick_rights(self):
        utils = self.utils

        self.assertTrue(await utils.has_kick_rights(10, 20))
        self.assertTrue(await utils.has_kick_rights(10, 30))
        self.assertFalse(await utils.has_kick_rights(20, 10))
        self.assertFalse(await utils.has_kick_rights(30, 10))

    async def test_broadcast(self):
        utils = self.utils
        bot = DummyBot()

        with i18n.context():
            await utils.broadcast(
                bot,  # noqa
                LazyProxy(dummy_gettext, "Hello, {name}!", enable_cache=False),
                format_args={"name": "world"},
                exclude_ids=[20],
            )

        kb = types.InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    types.InlineKeyboardButton(
                        text="Show menu",
                        callback_data="show_menu",
                    )
                ]
            ]
        )

        self.assertTrue(len(bot.calls) == 2)
        self.assertEqual(bot.calls[0], (10, "Hello, world! eo", kb))
        self.assertEqual(bot.calls[1], (30, "Hello, world! es", kb))


if __name__ == "__main__":
    unittest.main()
