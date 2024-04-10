import unittest

from travelagent.services.osm import (
    AreaNotFound,
    AreaTooManyResults,
    geocode_area,
    resolve_area_query,
)


class OSMTestCase(unittest.TestCase):
    def test_query_unknown_area(self):
        self.assertRaises(AreaNotFound, resolve_area_query, "asdasd")
        self.assertRaises(AreaNotFound, resolve_area_query, "adsgdsfgasg")
        self.assertRaises(
            AreaNotFound, resolve_area_query, "ultimativelyunknownarea"
        )

    def test_query_too_much(self):
        self.assertRaises(AreaTooManyResults, resolve_area_query, "Moscow")

    def test_query_moscow(self):
        result = resolve_area_query("Russia, Moscow")
        self.assertEqual(result["name"], "Москва")
        self.assertEqual(result["osm_id"], 2555133)

    def test_query_ognikovo(self):
        result = resolve_area_query("Огниково")
        self.assertEqual(result["name"], "Огниково")
        self.assertEqual(result["osm_id"], 12434364)

    def test_geocode_newyork(self):
        lat, lon = geocode_area(175905)
        self.assertEqual(round(lat), 40)
        self.assertEqual(round(lon), -74)

    def test_geocode_ognikovo(self):
        lat, lon = geocode_area(12434364)
        self.assertEqual(round(lat), 56)
        self.assertEqual(round(lon), 37)


if __name__ == "__main__":
    unittest.main()
