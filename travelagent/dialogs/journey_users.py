import logging

import pytz
from aiogram import types
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import (
    Button,
    ScrollingGroup,
    Select,
    SwitchTo,
    Url,
)
from aiogram_dialog.widgets.text import Const, Format
from babel.dates import format_datetime
from tortoise.expressions import Q

from travelagent.misc import BACK, BACK_STATE
from travelagent.models import Journey, JourneyInvite, User
from travelagent.services.journey import JourneyUtils
from travelagent.states import JourneyUsersSG
from travelagent.utils import lazy_gettext as _
from travelagent.widgets import Emojize, StartWithSameData

logger = logging.getLogger(__name__)


async def journey_list_getter(dialog_manager: DialogManager, user: User, **__):
    journey_id = dialog_manager.start_data["journey_id"]
    journey = await Journey.get(id=journey_id)

    return {
        "journey": journey,
        "user": user,
        "users": await journey.users.filter(~Q(id=user.id)),
    }


async def open_journey_user(__, ___, manager: DialogManager, user_id: str):
    await manager.start(
        JourneyUsersSG.user_view,
        data={
            "journey_id": manager.start_data["journey_id"],
            "user_id": int(user_id),
        },
    )


async def journey_view_user_getter(
    dialog_manager: DialogManager, user: User, **__
):
    journey_id = dialog_manager.start_data["journey_id"]
    user_id = dialog_manager.start_data["user_id"]

    journey = await Journey.get(id=journey_id)
    target_user = await User.get(id=user_id)

    return {
        "journey": journey,
        "user": target_user,
        "can_kick_user": await JourneyUtils(journey).has_kick_rights(
            user.id, target_user.id
        ),
    }


async def kick_from_journey(
    call: types.CallbackQuery, __, dialog_manager: DialogManager
):
    journey_id = dialog_manager.start_data["journey_id"]
    user_id = dialog_manager.start_data["user_id"]

    journey = await Journey.get(id=journey_id)
    target_user = await User.get(id=user_id)

    assert await JourneyUtils(journey).has_kick_rights(
        call.from_user.id, target_user.id
    )

    await journey.users.remove(target_user)
    await call.answer("User has been kicked from the journey.")
    await dialog_manager.done()


async def journey_invite_link_getter(
    dialog_manager: DialogManager, user: User, **__
):
    journey_id = dialog_manager.start_data["journey_id"]

    invite, __ = await JourneyInvite.get_or_create(
        journey_id=journey_id, owner=user
    )
    if not invite.valid:
        await invite.delete()
        invite = await JourneyInvite.create(journey_id=journey_id, owner=user)

    bot = dialog_manager.middleware_data["bot"]
    me = await bot.me()

    return {
        "user": user,
        "invite_link": f"https://t.me/{me.username}?start=inv_{invite.id}",
        "expires_at": format_datetime(
            invite.expires_at, "long", pytz.UTC, user.lang_code
        ),
    }


async def revoke_invite_link(
    call: types.CallbackQuery, __, dialog_manager: DialogManager
):
    journey_id = dialog_manager.start_data["journey_id"]
    await JourneyInvite.filter(
        journey_id=journey_id, owner_id=call.from_user.id
    ).delete()


journey_users_dialog = Dialog(
    Window(
        Format(_("Journey {journey.name} › Participants")),
        ScrollingGroup(
            StartWithSameData(
                Emojize(_(":link: Invite user")),
                id="invite",
                state=JourneyUsersSG.invite,
            ),
            Url(
                Format(_("Me [{user.name}]")),
                Format("tg://user?id={user.id}"),
            ),
            Select(
                Format("{item.name}"),
                id="s_users",
                item_id_getter=lambda u: u.id,
                items="users",
                on_click=open_journey_user,
            ),
            id="scroll_users",
            width=1,
            height=6,
            hide_on_single_page=True,
        ),
        BACK,
        state=JourneyUsersSG.list,
        getter=journey_list_getter,
    ),
    Window(
        Format("Journey {journey.name} › Participant {user.name}"),
        Url(
            Const(_("Open profile")),
            Format("tg://user?id={user.id}"),
        ),
        SwitchTo(
            Emojize(_(":name_badge: Kick from journey")),
            id="kick_from_journey",
            state=JourneyUsersSG.user_kick_confirm,
            when="can_kick_user",
        ),
        BACK,
        state=JourneyUsersSG.user_view,
        getter=journey_view_user_getter,
    ),
    Window(
        Format(
            _(
                "Are you sure you want to kick {user.name} from the journey "
                "{journey.name}?\n\n"
                "They will lose access to the journey and all its data. "
                "But they can rejoin if they will get the invite link again."
            )
        ),
        Button(
            Emojize(_(":name_badge: Kick")),
            id="kick",
            on_click=kick_from_journey,
        ),
        BACK_STATE,
        state=JourneyUsersSG.user_kick_confirm,
        getter=journey_view_user_getter,
    ),
    Window(
        Emojize(
            Format(
                _(
                    ":link: Invite another user to the journey.\n"
                    "Share the link below with the user you want to invite.\n\n"
                    "{invite_link}\n\n"
                    "The link will expire at {expires_at}. The link can be used several times."
                )
            )
        ),
        Button(
            Const(_("Revoke link")),
            id="revoke_link",
            on_click=revoke_invite_link,
        ),
        BACK,
        state=JourneyUsersSG.invite,
        getter=journey_invite_link_getter,
    ),
)
