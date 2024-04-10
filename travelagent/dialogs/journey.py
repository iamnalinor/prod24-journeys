import logging

from aiogram import F
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import (
    Button,
    ScrollingGroup,
    Select,
    Start,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Case, Const, Format

from travelagent.misc import BACK, BACK_STATE
from travelagent.models import Journey, User
from travelagent.states import (
    JourneyCreateSG,
    JourneyLocationsSG,
    JourneySG,
    JourneyUsersSG,
)
from travelagent.utils import lazy_gettext as _
from travelagent.widgets import Emojize, StartWithSameData

logger = logging.getLogger(__name__)


async def journeys_getter(user: User, **__):
    return {
        "journeys": await Journey.filter(users=user),
    }


async def open_journey(__, ___, manager: DialogManager, journey_id: str):
    await manager.start(JourneySG.view, data={"journey_id": int(journey_id)})


async def journey_view_getter(dialog_manager: DialogManager, **__):
    journey_id = dialog_manager.start_data["journey_id"]
    journey = await Journey.get(id=journey_id)

    user = dialog_manager.middleware_data["user"]

    # Close dialog if the user got kicked
    if (await journey.users.filter(id=user.id).count()) == 0:
        await dialog_manager.done()
        return {}

    data = {"journey": journey}
    for field in ("locations", "notes", "users"):
        data[f"{field}_count"] = await getattr(journey, field).all().count()

    return data


async def leave_from_journey(__, ___, manager: DialogManager):
    journey_id = manager.start_data["journey_id"]
    journey = await Journey.get(id=journey_id)
    user = manager.middleware_data["user"]

    await journey.users.remove(user)

    if (await journey.users.all().count()) == 0:
        await journey.delete()

    await manager.done()


journey_dialog = Dialog(
    Window(
        Const(_("List of your journeys:")),
        ScrollingGroup(
            Start(
                Emojize(_(":plus: New journey")),
                id="new_journey",
                state=JourneyCreateSG.name,
            ),
            Select(
                Format("{item.name}"),
                id="s_journeys",
                item_id_getter=lambda j: j.id,
                items="journeys",
                on_click=open_journey,
            ),
            id="scroll_journeys",
            width=1,
            height=5,
            hide_on_single_page=True,
        ),
        BACK,
        getter=journeys_getter,
        state=JourneySG.list,
    ),
    Window(
        Emojize(
            Format(
                _(
                    ":vertical_traffic_light: Journey {journey.name} › Review & edit"
                )
            )
        ),
        StartWithSameData(
            Emojize(Format(_(":Micronesia: Locations [{locations_count}]"))),
            id="view_locations",
            state=JourneyLocationsSG.list,
        ),
        Button(
            Emojize(
                Format(
                    _(":notebook_with_decorative_cover: Notes [{notes_count}]")
                )
            ),
            id="view_notes",
        ),
        StartWithSameData(
            Format(_("Participants [{users_count}]")),
            id="view_users",
            state=JourneyUsersSG.list,
        ),
        SwitchTo(
            Case(
                {
                    True: Emojize(_(":stop_sign: Delete journey")),
                    False: Emojize(_(":minus: Leave journey")),
                },
                selector=F["users_count"] == 1,
            ),
            id="leave_from_journey",
            state=JourneySG.confirm_leave,
        ),
        BACK,
        getter=journey_view_getter,
        state=JourneySG.view,
    ),
    Window(
        Case(
            {
                True: Format(
                    _(
                        "You are deleting journey {journey.name}. "
                        "This action cannot be undone.\n\n"
                        "Are you sure?"
                    )
                ),
                False: Format(
                    _(
                        "You are leaving journey {journey.name}. "
                        "You can return back if you obtain an invite link again.\n\n"
                        "Are you sure?"
                    )
                ),
            },
            selector=F["users_count"] == 1,
        ),
        Button(
            Const(_("Yes, I'm sure")),
            id="confirm_leave",
            on_click=leave_from_journey,
        ),
        BACK_STATE,
        getter=journey_view_getter,
        state=JourneySG.confirm_leave,
    ),
)
