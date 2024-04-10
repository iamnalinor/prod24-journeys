import logging

from aiogram import F, types
from aiogram.filters import Command, CommandStart, ExceptionTypeFilter
from aiogram_dialog import Dialog, DialogManager, ShowMode, StartMode, Window
from aiogram_dialog.api.exceptions import (
    DialogStackOverflow,
    OutdatedIntent,
    UnknownIntent,
    UnknownState,
)
from aiogram_dialog.widgets.kbd import Start
from aiogram_dialog.widgets.text import Format
from emoji import emojize

from travelagent.config import LOCALES
from travelagent.misc import dp
from travelagent.models import JourneyInvite, User
from travelagent.states import (
    ConfirmJoinSG,
    JourneySG,
    MainSG,
    RegisterSG,
    SettingsSG,
)
from travelagent.utils import lazy_gettext as _
from travelagent.utils import parse_ietf_tag
from travelagent.widgets import Emojize

logger = logging.getLogger(__name__)


@dp.message(CommandStart())
async def start_cmd(
    message: types.Message, user: User, dialog_manager: DialogManager
):
    if user.lang_code is None:
        user.lang_code = parse_ietf_tag(message.from_user.language_code)
        await user.save()

        logger.debug(
            "Language for user %d has been set to %s", user.id, user.lang_code
        )

        i18n = dialog_manager.middleware_data["i18n"]
        i18n.current_locale = user.lang_code

        locale = LOCALES[user.lang_code]
        await message.answer(
            emojize(
                _(
                    "Language has been set to {locale.flag} {locale.name}. "
                    "You can change it in /settings."
                ).format(locale=locale)
            )
        )

    if message.text.startswith("/start inv_"):
        inv_code = message.text.split("_")[1]
        invite = await JourneyInvite.get_or_none(id=inv_code).prefetch_related(
            "journey"
        )
        if invite is None or not invite.valid:
            await message.answer(
                _(
                    "Invite code is invalid. "
                    "Probably, it has expired or revoked."
                )
            )
        elif (await invite.journey.users.filter(id=user.id).count()) > 0:
            await message.answer(_("You have already joined this journey."))
        else:
            await dialog_manager.start(
                ConfirmJoinSG.intro,
                data={"journey_id": invite.journey.id, "invite_id": invite.id},
            )
            return

    if not user.registered:
        await dialog_manager.start(RegisterSG.age, mode=StartMode.RESET_STACK)
        return

    await dialog_manager.start(MainSG.intro, mode=StartMode.RESET_STACK)


@dp.message(Command("show"))
@dp.callback_query(F.data == "show_menu")
async def show_cmd(update, dialog_manager: DialogManager):
    await dialog_manager.show(ShowMode.SEND)


@dp.errors(
    ExceptionTypeFilter(
        UnknownIntent, OutdatedIntent, UnknownState, DialogStackOverflow
    )
)
async def error_handler(exception: types.Update, dialog_manager: DialogManager):
    logger.exception("Error in dialog manager for user")

    await dialog_manager.reset_stack()

    update = exception.update.message or exception.update.callback_query or None
    if update:
        await update.answer("An error occurred. Please, press /start.")


start_dialog = Dialog(
    Window(
        Format(_("Hello, {event.from_user.first_name}!")),
        Start(
            Emojize(_(":earth_africa: Journeys")),
            id="show_journeys",
            state=JourneySG.list,
        ),
        Start(
            Emojize(_(":gear: Settings")),
            id="settings",
            state=SettingsSG.intro,
        ),
        state=MainSG.intro,
    ),
)
