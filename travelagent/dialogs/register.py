import logging

from aiogram import types
from aiogram.enums import ChatType, ContentType
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Back, Button, Next
from aiogram_dialog.widgets.text import Const

from travelagent.misc import BACK, HOME
from travelagent.services.osm import AreaSearchError, resolve_area_query
from travelagent.states import RegisterSG
from travelagent.utils import lazy_gettext as _
from travelagent.utils import maybe_next
from travelagent.widgets import Emojize

logger = logging.getLogger(__name__)


async def save_age(message: types.Message, __, manager: DialogManager):
    try:
        age = int(message.text)
        if age < 0 or age > 200:
            raise ValueError
    except ValueError:
        await message.answer(_("Please enter a valid age."))
        return

    user = manager.middleware_data["user"]
    await user.update_from_dict({"age": age}).save()

    await maybe_next(manager)


async def bio_getter(event_from_user: types.User, event_chat: types.Chat, **__):
    # normally bot should run only in PM
    assert (
        event_from_user.id == event_chat.id
        and event_chat.type == ChatType.PRIVATE
    )

    return {
        "has_bio": bool(event_chat.bio),
    }


async def save_bio(
    update: types.Message | types.CallbackQuery,
    __,
    manager: DialogManager,
):
    if isinstance(update, types.CallbackQuery):
        assert update.message.chat == ChatType.PRIVATE
        bio = update.message.chat.bio
    else:
        bio = update.text
    assert bio

    user = manager.middleware_data["user"]
    await user.update_from_dict({"bio": bio}).save()

    await maybe_next(manager)


async def location_getter(event_chat: types.Chat, **__):
    await event_chat.bot.send_message(
        event_chat.id,
        _("Alright."),
        reply_markup=types.ReplyKeyboardMarkup(
            keyboard=[
                [
                    types.KeyboardButton(
                        text=_("Send location"), request_location=True
                    )
                ]
            ],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )

    return {}


async def save_home_location(
    message: types.Message,
    __,
    manager: DialogManager,
):
    query = (
        f"{message.location.latitude},{message.location.longitude}"
        if message.location
        else message.text
    )

    try:
        area = resolve_area_query(query)
    except AreaSearchError as e:
        await message.answer(e.as_i18n_string())
        return

    user = manager.middleware_data["user"]
    await user.update_from_dict({"home_area_id": area["osm_id"]}).save()

    await message.answer(
        _(
            "Area {name} has been set. If there's an error, return back and try again."
        ).format(name=area["display_name"]),
        reply_markup=types.ReplyKeyboardRemove(),
    )
    await maybe_next(manager)


register_dialog = Dialog(
    Window(
        Const(_("Welcome to Travel Agent!\nWhat is your age?")),
        MessageInput(save_age, ContentType.TEXT),
        state=RegisterSG.age,
        preview_add_transitions=[Next()],
    ),
    Window(
        Const(
            _(
                "Write a short bio about yourself.\n"
                "For example: 23 y.o. designer from San Francisco. Big fan of traveling and photography."
            )
        ),
        MessageInput(save_bio, ContentType.TEXT),
        Button(
            Const(_("Copy from profile")),
            id="copy_from_profile",
            on_click=save_bio,
            when="has_bio",
        ),
        BACK,
        getter=bio_getter,
        state=RegisterSG.bio,
        preview_add_transitions=[Next()],
        preview_data={"has_bio": True},
    ),
    Window(
        Const(
            _(
                "Please select your home location. Either press the button below or type it in.\n\n"
                "This will be start point for your journeys."
            )
        ),
        MessageInput(
            save_home_location,
            [ContentType.TEXT, ContentType.LOCATION],
        ),
        state=RegisterSG.home,
        getter=location_getter,
        preview_add_transitions=[Next()],
    ),
    Window(
        Emojize(_(":party_popper: The registration is completed!")),
        Back(Const(_("‹ Change location"))),
        HOME,
        state=RegisterSG.outro,
    ),
)
