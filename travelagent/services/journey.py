import asyncio
import logging

from aiogram import Bot, types
from aiogram.exceptions import TelegramAPIError
from aiogram.utils.i18n import I18n
from babel.support import LazyProxy

from travelagent.models import Journey
from travelagent.utils import lazy_gettext as _


class JourneyUtils:
    def __init__(self, journey: Journey):
        self.journey = journey

    async def has_kick_rights(self, source_id: int, target_id: int) -> bool:
        """
        Check that `source` user has rights to kick `target` user.
        `Source` can kick target only and only if `source` joined before target. Explained in README.
        :param source_id: Source's user id
        :param target_id: Target's user id
        :return: True if the source can kick target, False otherwise
        """
        assert source_id != target_id
        users = await self.journey.users.all().values("id")
        return users.index({"id": source_id}) < users.index({"id": target_id})

    async def broadcast(
        self,
        bot: Bot,
        text: LazyProxy | None,
        format_args: dict[str, str] | None = None,
        exclude_ids: list[int] | None = None,
    ):
        """
        Broadcast a message to all users in the journey. Either media or text must be set.
        :param bot: The bot to send the message from
        :param text: Text to send
        :param format_args: If needed, the text can be formatted
        :param exclude_ids: List of user ids to exclude from the broadcast
        """

        exclude_ids = exclude_ids or []
        format_args = format_args or {}

        for user in await self.journey.users.all():
            if user.id in exclude_ids:
                continue

            with I18n.get_current().use_locale(user.lang_code):
                keyboard = types.InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            types.InlineKeyboardButton(
                                text=str(_("Show menu")),
                                callback_data="show_menu",
                            )
                        ]
                    ]
                )

                try:
                    await bot.send_message(
                        user.id,
                        text.format_map(format_args),
                        reply_markup=keyboard,
                    )
                except TelegramAPIError as e:
                    logging.error(f"Failed to send message to {user.id}: {e}")

            await asyncio.sleep(0.3)
