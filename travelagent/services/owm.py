from datetime import date
from typing import Any

import aiohttp

from travelagent.config import OWM_APPID


async def get_forecast(
    lat: float, lon: float, lang_code: str = "en"
) -> dict[date, dict[str, Any]]:
    """
    Get weather forecast for the given location.
    :param lat: Latitude
    :param lon: Longitude
    :param lang_code: Optional, user language code
    :return: dict with date as key and forecast data as value
    """

    async with (
        aiohttp.ClientSession() as session,
        session.get(
            "https://api.openweathermap.org/data/2.5/forecast",
            params={
                "lat": lat,
                "lon": lon,
                "appid": OWM_APPID,
                "units": "metric",
                "lang": lang_code,
            },
        ) as resp,
    ):
        result: dict[date, dict[str, Any]] = {}
        data = await resp.json()

        # fill primarily with 15:00 forecasts
        for item in data["list"]:
            if "15:00" not in item["dt_txt"]:
                continue
            dt = date.fromtimestamp(item["dt"])
            result[dt] = item

        # fill the rest
        for item in data["list"]:
            dt = date.fromtimestamp(item["dt"])
            if dt not in result:
                result[dt] = item

        return dict(sorted(result.items()))
