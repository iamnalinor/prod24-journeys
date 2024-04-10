import logging
import operator

from aiogram import types
from aiogram.filters import Command
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import Column, Radio, Start
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.widget_event import SimpleEventProcessor

from travelagent.config import DEFAULT_LOCALE, LOCALES
from travelagent.misc import BACK, dp
from travelagent.models import User
from travelagent.states import RegisterSG, SettingsSG
from travelagent.utils import lazy_gettext as _
from travelagent.widgets import Emojize

logger = logging.getLogger(__name__)


@dp.message(Command("settings"))
async def settings_cmd(
    message: types.Message,
    dialog_manager: DialogManager,
):
    if dialog_manager.current_context().state in SettingsSG:
        await dialog_manager.show()
        return

    await dialog_manager.start(SettingsSG.intro)


async def locales_getter(dialog_manager: DialogManager, user: User, **__):
    lang_code = user.lang_code or DEFAULT_LOCALE

    radio = dialog_manager.find("r_locales")
    await radio.set_checked(lang_code)

    return {
        "locales": LOCALES.values(),
    }


async def set_lang_code(
    _,
    __,
    dialog_manager: DialogManager,
    lang_code: str,
):
    user: User = dialog_manager.middleware_data["user"]
    user.lang_code = lang_code
    await user.save()

    i18n = dialog_manager.middleware_data["i18n"]
    i18n.current_locale = lang_code

    logger.debug(
        "Language for user %d has been set to %s", user.id, user.lang_code
    )


settings_dialog = Dialog(
    Window(
        Emojize(_(":gear: Settings")),
        Start(
            Const(_("Change language")),
            id="change_lang",
            state=SettingsSG.choose_lang,
        ),
        Start(
            Const(_("Change bio")),
            id="change_bio",
            state=RegisterSG.bio,
            data={"single": True},
        ),
        Start(
            Const(_("Change age")),
            id="change_age",
            state=RegisterSG.age,
            data={"single": True},
        ),
        Start(
            Const(_("Change home location")),
            id="change_home",
            state=RegisterSG.home,
            data={"single": True},
        ),
        BACK,
        state=SettingsSG.intro,
    ),
    Window(
        Emojize(_(":white_flag: Choose your language:")),
        Column(
            Radio(
                Emojize(Format("• {item[1]} {item[2]} •")),
                Emojize(Format("{item[1]} {item[2]}")),
                id="r_locales",
                item_id_getter=operator.itemgetter(0),
                items="locales",
                on_state_changed=SimpleEventProcessor(set_lang_code),
            ),
        ),
        BACK,
        getter=locales_getter,
        state=SettingsSG.choose_lang,
    ),
)
