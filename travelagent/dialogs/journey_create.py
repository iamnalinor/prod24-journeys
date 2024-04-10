import datetime
import logging

from aiogram import F, types
from aiogram.enums import ContentType
from aiogram_dialog import Dialog, DialogManager, ShowMode, Window
from aiogram_dialog.widgets.input import MessageInput, TextInput
from aiogram_dialog.widgets.kbd import (
    Button,
    Calendar,
    CalendarConfig,
    Next,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Case, Const
from aiogram_dialog.widgets.widget_event import ensure_event_processor
from babel.dates import format_timedelta

from travelagent.misc import BACK, BACK_STATE, CANCEL
from travelagent.models import Journey, JourneyLocation, JourneyNote, User
from travelagent.services.osm import AreaSearchError, resolve_area_query
from travelagent.states import JourneyCreateSG, JourneyLocationsSG, JourneySG
from travelagent.utils import lazy_gettext as _
from travelagent.widgets import Emojize

logger = logging.getLogger(__name__)


async def journey_name_filter(message: types.Message, user: User, *__):
    name_exists = await Journey.filter(name=message.text, users=user).exists()
    if name_exists:
        await message.answer(_("This name is already taken. Try another one."))
        return False
    return True


@ensure_event_processor
async def location_name_handler(
    message: types.Message,
    __,
    manager: DialogManager,
):
    try:
        location = resolve_area_query(message.text)
    except AreaSearchError as e:
        await message.answer(e.as_i18n_string())
        return

    manager.dialog_data["current_loc_query"] = message.text
    manager.dialog_data["current_loc_area"] = location
    manager.dialog_data["choose_dates_state"] = "start"
    await message.answer(
        _("Selected location: {name}. Press Back if there's an error.").format(
            name=location["display_name"]
        ),
    )
    await manager.next()


async def location_dates_getter(dialog_manager: DialogManager, **__):
    return {
        "location_dates_state": dialog_manager.dialog_data[
            "choose_dates_state"
        ],
    }


async def location_date_selected(
    call: types.CallbackQuery,
    __,
    manager: DialogManager,
    date: datetime.date,
):
    state = manager.dialog_data["choose_dates_state"]

    if state == "start":
        if date < datetime.date.today():
            await call.answer(
                _("You can't choose a date in the past. Please, try again."),
                show_alert=True,
            )
            return

        manager.dialog_data["location_start_date"] = date.isoformat()
        manager.dialog_data["choose_dates_state"] = "end"
        return

    start_date = date.fromisoformat(manager.dialog_data["location_start_date"])
    end_date = date

    if start_date >= end_date:
        await call.answer(
            _(
                "Departure date should be later than arrival date. Please, try again."
            ),
            show_alert=True,
        )
        return

    area = manager.dialog_data["current_loc_area"]
    loc = await JourneyLocation.create(
        name=manager.dialog_data["current_loc_query"],
        address=area["display_name"],
        area_id=area["osm_id"],
        start_date=start_date,
        end_date=end_date,
    )

    start_data = manager.start_data or {}
    if start_data.get("single"):
        journey = await Journey.get(id=start_data["journey_id"])
        await journey.locations.add(loc)
        await manager.done(show_mode=ShowMode.NO_UPDATE)
        await manager.start(
            JourneyLocationsSG.view,
            data={"journey_id": journey.id, "location_id": loc.id},
            show_mode=ShowMode.SEND,
        )
        return

    manager.dialog_data.setdefault("locations", [])
    manager.dialog_data["locations"].append(loc.id)

    if len(manager.dialog_data["locations"]) >= 20:
        await call.message.answer(
            _(
                "You've already added 20 locations. "
                "For performance reasons, you can't add more.\n\n"
                "You can create separate journey if you want to add more locations."
            )
        )
        await manager.switch_to(JourneyCreateSG.outro, show_mode=ShowMode.SEND)
        return

    user = manager.middleware_data["user"]

    await call.message.answer(
        _(
            "You've added location {name} for {delta}. How about another one?"
        ).format(
            name=loc.name,
            delta=format_timedelta(
                loc.duration,
                granularity="day",
                threshold=1,
                locale=user.lang_code,
            ),
        ),
    )
    await manager.switch_to(
        JourneyCreateSG.location_name, show_mode=ShowMode.SEND
    )


async def journey_create(__, ___, manager: DialogManager):
    user = manager.middleware_data["user"]
    journey = await Journey.create(
        name=manager.find("i_journey_name").get_value(),
    )
    await journey.users.add(user)

    if description := manager.find("i_journey_description").get_value():
        await journey.notes.add(
            await JourneyNote.create(author=user, text=description)
        )

    # because Done button is shown with at least one location,
    # we can safely assume that locations are present
    locations = await JourneyLocation.filter(
        id__in=manager.dialog_data["locations"]
    )
    locations = sorted(locations, key=lambda loc: loc.start_date)
    await journey.locations.add(*locations)

    await manager.done(show_mode=ShowMode.NO_UPDATE)
    await manager.start(JourneySG.view, {"journey_id": journey.id})


journey_create_dialog = Dialog(
    Window(
        Emojize(
            _(
                "Going somewhere? Let's :memo: organize everything.\n\n"
                "Enter the unique name of your journey:"
            )
        ),
        BACK,
        TextInput(
            "i_journey_name",
            filter=journey_name_filter,
            on_success=Next(),
        ),
        state=JourneyCreateSG.name,
    ),
    Window(
        Const(_("Enter a brief description of your journey:")),
        TextInput("i_journey_description", on_success=Next()),
        Next(Const(_("Skip"))),
        BACK_STATE,
        state=JourneyCreateSG.description,
    ),
    Window(
        Const(_("Enter the name of location you want to visit:")),
        SwitchTo(
            Emojize(_(":check_mark_button: Done")),
            id="journey_create_done",
            state=JourneyCreateSG.outro,
            when=F["dialog_data"]["locations"],
        ),
        CANCEL,
        MessageInput(location_name_handler, ContentType.TEXT),
        state=JourneyCreateSG.location_name,
    ),
    Window(
        Case(
            {
                "start": Emojize(
                    _(
                        ":airplane_arrival: Choose the arrival date of this location:",
                    )
                ),
                "end": Emojize(
                    _(
                        ":airplane_departure: Choose the departure date of this location:",
                    )
                ),
            },
            selector=F["dialog_data"]["choose_dates_state"],
        ),
        Calendar(
            id="location_date",
            on_click=location_date_selected,
            config=CalendarConfig(datetime.date(2024, 1, 1)),
        ),
        BACK_STATE,
        getter=location_dates_getter,
        state=JourneyCreateSG.location_dates,
    ),
    Window(
        Const(
            _(
                "Now you're ready to go! Click the button below to create your journey."
            )
        ),
        Button(
            Emojize(_(":fire: Create journey")),
            id="journey_open",
            on_click=journey_create,
        ),
        BACK_STATE,
        state=JourneyCreateSG.outro,
    ),
)
