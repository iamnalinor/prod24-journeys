import operator
from datetime import date

from aiogram import F, types
from aiogram_dialog import Dialog, DialogManager, Window
from aiogram_dialog.widgets.kbd import (
    Button,
    ScrollingGroup,
    Select,
    SwitchTo,
    Url,
)
from aiogram_dialog.widgets.text import Case, Const, Format, Jinja, Multi
from babel.dates import format_date, format_timedelta

from travelagent.misc import BACK, BACK_STATE
from travelagent.models import Journey, JourneyLocation, User
from travelagent.services.osm import geocode_area
from travelagent.services.owm import get_forecast
from travelagent.states import JourneyCreateSG, JourneyLocationsSG
from travelagent.utils import lazy_gettext as _
from travelagent.widgets import Emojize, StartWithSameData


async def locations_list_getter(
    dialog_manager: DialogManager, user: User, **__
):
    journey_id = dialog_manager.start_data["journey_id"]
    journey = await Journey.get(id=journey_id)
    locations = await journey.locations.all().order_by("start_date")

    locale = user.lang_code

    locations = [
        (
            loc.id,
            "{name} [{start} - {end}]".format(  # noqa: UP032
                name=loc.name[:20],
                start=format_date(loc.start_date, "short", locale),
                end=format_date(loc.end_date, "short", locale),
            ),
        )
        for loc in locations
    ]

    return {
        "journey": journey,
        "locations": locations,
    }


async def open_location(__, ___, manager: DialogManager, location_id: str):
    await manager.start(
        JourneyLocationsSG.view,
        {
            **manager.start_data,
            "location_id": str(location_id),
        },
    )


async def location_getter(dialog_manager: DialogManager, user: User, **__):
    journey_id = dialog_manager.start_data["journey_id"]
    location_id = dialog_manager.start_data["location_id"]

    journey = await Journey.get(id=journey_id)
    location = await JourneyLocation.get(id=location_id)

    locations = (
        await journey.locations.all()
        .order_by("start_date")
        .values("id", "area_id")
    )
    prev_index = (
        locations.index({"id": location.id, "area_id": location.area_id}) - 1
    )
    if prev_index >= 0:
        print(locations, prev_index, locations[prev_index])
        prev_coords = geocode_area(locations[prev_index]["area_id"])
    else:
        prev_coords = geocode_area(user.home_area_id)

    current_coords = geocode_area(location.area_id)

    route_url = (
        "https://www.openstreetmap.org/directions?engine=fossgis_osrm_car&"
        f"route={prev_coords[0]},{prev_coords[1]};{current_coords[0]},{current_coords[1]}"
    )

    locale = user.lang_code

    return {
        "journey": journey,
        "location": location,
        "start_date": format_date(location.start_date, "short", locale),
        "end_date": format_date(location.end_date, "short", locale),
        "duration": format_timedelta(
            location.duration,
            granularity="day",
            threshold=1,
            format="long",
            locale=locale,
        ),
        "route_url": route_url,
    }


async def delete_location(
    call: types.CallbackQuery, __, manager: DialogManager
):
    journey_id = manager.start_data["journey_id"]
    location_id = manager.start_data["location_id"]

    journey = await Journey.get(id=journey_id).prefetch_related("locations")

    if len(journey.locations) == 1:
        await call.answer(
            _(
                "You can't delete this location as it's the only one in the journey. "
                "Consider adding another location or deleting the whole journey instead."
            ),
            show_alert=True,
        )
        return

    await JourneyLocation.filter(id=location_id).delete()
    await manager.done()


async def weather_getter(dialog_manager: DialogManager, user: User, **__):
    journey_id = dialog_manager.start_data["journey_id"]
    location_id = dialog_manager.start_data["location_id"]

    journey = await Journey.get(id=journey_id)
    location = await JourneyLocation.get(id=location_id)

    lat, lon = geocode_area(location.area_id)
    forecast = await get_forecast(lat, lon, user.lang_code)

    filtered_forecast = {
        format_date(forecast_date, "short", user.lang_code): item
        for forecast_date, item in forecast.items()
        if location.start_date <= forecast_date <= location.end_date
    }

    no_data_reason = (
        None
        if len(filtered_forecast) > 0
        else "early"
        if date.today() < location.start_date
        else "late"
    )

    return {
        "journey": journey,
        "location": location,
        "forecast": filtered_forecast,
        "no_data_reason": no_data_reason,
    }


journey_locations_dialog = Dialog(
    Window(
        Format(_("Journey {journey.name} › Locations")),
        ScrollingGroup(
            StartWithSameData(
                Emojize(_(":plus: Add location")),
                id="invite",
                state=JourneyCreateSG.location_name,
                data={"single": True},
                when=F["locations"].len() < 20,
            ),
            Select(
                Format("{item[1]}"),
                id="s_locations",
                item_id_getter=operator.itemgetter(0),
                items="locations",
                on_click=open_location,
            ),
            id="scroll_locations",
            width=1,
            height=6,
            hide_on_single_page=True,
        ),
        BACK,
        state=JourneyLocationsSG.list,
        getter=locations_list_getter,
    ),
    Window(
        Format(
            _(
                "Journey {journey.name} › Location {location.name}\n\n"
                "Arrival date: {start_date}\n"
                "Departure date: {end_date}\n"
                "Duration: {duration}\n\n"
                "Address: {location.address}"
            )
        ),
        StartWithSameData(
            Emojize(_(":sun_behind_small_cloud: Weather")),
            id="weather",
            state=JourneyLocationsSG.weather,
        ),
        Url(Const(_("Open route to this location")), Format("{route_url}")),
        SwitchTo(
            Emojize(_(":stop_sign: Delete location")),
            id="delete_location",
            state=JourneyLocationsSG.confirm_delete,
        ),
        BACK,
        state=JourneyLocationsSG.view,
        getter=location_getter,
    ),
    Window(
        Format(
            _(
                "Are you sure you want to delete location {location.name} "
                "from journey {journey.name}?\n"
                "You can always add it back."
            )
        ),
        Button(
            Const(_("Yes, delete")),
            id="confirm_delete",
            on_click=delete_location,
        ),
        BACK_STATE,
        getter=location_getter,
        state=JourneyLocationsSG.confirm_delete,
    ),
    Window(
        Multi(
            Format(
                _(
                    "Journey {journey.name} › Location {location.name} > Weather forecast"
                )
            ),
            Jinja(
                """
{% for date, item in forecast.items() %}
{{ date }}: {{ item.main.temp }}°C, {{ item.weather[0].description }}
{% endfor %}
"""
            ),
            Case(
                {
                    "early": Const(
                        _(
                            "Weather data is available only for 5 days in future. "
                            "Check back at several days before the arrival."
                        )
                    ),
                    "late": Const(
                        _(
                            "The location departure date is in the past, so no forecast is available.",
                        )
                    ),
                },
                selector="no_data_reason",
                when=F["forecast"].len() == 0,
            ),
            sep="\n\n",
        ),
        BACK,
        state=JourneyLocationsSG.weather,
        getter=weather_getter,
    ),
)
