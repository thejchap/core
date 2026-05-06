"""Tryke fixtures for Zamg integration tests."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import fixture

TEST_STATION_ID = "11240"
TEST_STATION_NAME = "Graz/Flughafen"


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch("homeassistant.components.zamg.async_setup_entry", return_value=True):
        yield


@fixture
def mock_zamg() -> Generator[MagicMock]:
    """Return a mocked Zamg client."""
    with patch(
        "homeassistant.components.zamg.config_flow.ZamgData", autospec=True
    ) as zamg_mock:
        zamg = zamg_mock.return_value
        zamg.update.return_value = {TEST_STATION_ID: {"Name": TEST_STATION_NAME}}
        zamg.zamg_stations.return_value = {
            TEST_STATION_ID: (46.99305556, 15.43916667, TEST_STATION_NAME),
            "11244": (46.8722229, 15.90361118, "BAD GLEICHENBERG"),
        }
        zamg.closest_station.return_value = TEST_STATION_ID
        zamg.get_data.return_value = TEST_STATION_ID
        zamg.get_station_name = TEST_STATION_NAME
        yield zamg
