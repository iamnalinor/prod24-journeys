from aiogram.utils.i18n import gettext as _
from OSMPythonTools.api import Api
from OSMPythonTools.nominatim import Nominatim
from OSMPythonTools.overpass import Overpass

nominatim = Nominatim()
api = Api()
overpass = Overpass()


class AreaSearchError(Exception):
    @staticmethod
    def as_i18n_string() -> str:
        return _("Failed to find the area. Try again later")


class AreaNotFound(AreaSearchError):
    @staticmethod
    def as_i18n_string() -> str:
        return _("No such area found. Try specifying more general query.")


class AreaTooManyResults(AreaSearchError):
    @staticmethod
    def as_i18n_string() -> str:
        return _(
            "Too many areas found. Try specifying more precise query (e.g. add the country name)."
        )


def resolve_area_query(query: str, max_limit: int = 5) -> dict:
    """
    Resolve the query via Nominatim API.

    :param max_limit: raise AreaTooManyResults if there's more than this number of results
    :param query: the query itself

    :raises AreaSearchError: if the query failed
    :raises AreaNotFound: if there's 0 results
    :raises AreaTooManyResults: if there are more than max_limit results

    :return: result from Nominatim API, including "name" and "osm_id" fields
    """

    try:
        areas = nominatim.query(query).toJSON()
    except Exception as e:
        raise AreaSearchError from e

    if len(areas) == 0:
        raise AreaNotFound

    if len(areas) > max_limit:
        raise AreaTooManyResults

    return areas[0]


def geocode_area(area_id: int) -> tuple[float, float]:
    """
    Get the coordinates of the area.

    :param area_id: Area id from resolve_area_query
    :return: latitude and longitude coordinates respectively
    """

    area = overpass.query(
        f"relation({area_id});out body;>;out skel qt;"
    ).toJSON()
    nodes = list(filter(lambda x: x["type"] == "node", area["elements"]))

    return nodes[0]["lat"], nodes[0]["lon"]
