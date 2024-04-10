import asyncio

from aiogram import types
from aiogram_dialog import Dialog, DialogManager, ShowMode, StartMode, Window
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.text import Const, Format

from travelagent.misc import CANCEL
from travelagent.models import Journey, JourneyInvite
from travelagent.services.journey import JourneyUtils
from travelagent.states import ConfirmJoinSG, JourneySG, MainSG, RegisterSG
from travelagent.utils import lazy_gettext as _


async def journey_getter(dialog_manager: DialogManager, **__):
    journey_id = dialog_manager.start_data["journey_id"]
    journey = await Journey.get(id=journey_id)
    count = await journey.users.all().count()
    return {"journey": journey, "count": count}


async def confirm_join(call: types.CallbackQuery, ___, manager: DialogManager):
    journey_id = manager.start_data["journey_id"]
    journey = await Journey.get_or_none(id=journey_id)
    invite = await JourneyInvite.get_or_none(id=manager.start_data["invite_id"])

    if not journey or not invite or not invite.valid:
        await call.message.answer(
            _("Invite code is invalid. Probably, it has expired or revoked.")
        )
        await manager.done(ShowMode.SEND)
        return

    user = manager.middleware_data["user"]
    await journey.users.add(user)

    asyncio.ensure_future(
        JourneyUtils(journey).broadcast(
            call.bot,
            _("User {user.name} joined the journey"),
            format_args={"user": user},
            exclude_ids=[call.from_user.id],
        )
    )

    if not user.registered:
        await manager.start(RegisterSG.age, mode=StartMode.RESET_STACK)
        return

    await manager.start(
        MainSG.intro,
        show_mode=ShowMode.NO_UPDATE,
        mode=StartMode.RESET_STACK,
    )
    await manager.start(
        JourneySG.view,
        data={"journey_id": journey_id},
        show_mode=ShowMode.SEND,
    )


confirm_join_dialog = Dialog(
    Window(
        Format(
            _(
                "You're about to join the journey {journey.name} which has already {count} participants.\n\n"
                "You will receive an updates about the journey. Other participants will be notified about your join.\n"
                "You can leave the journey at any time.\n\n"
                "Do you want to join?"
            )
        ),
        Button(Const(_("Yes, join")), id="yes", on_click=confirm_join),
        CANCEL,
        getter=journey_getter,
        state=ConfirmJoinSG.intro,
    )
)
