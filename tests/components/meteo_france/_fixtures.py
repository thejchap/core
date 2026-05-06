"""Tryke fixtures for the Meteo-France integration."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from meteofrance_api.model import Place
from tryke import fixture

CITY_1_NAME = "La Clusaz"
CITY_1_LAT = 45.90417
CITY_1_LON = 6.42306
CITY_1 = Place(
    {
        "name": CITY_1_NAME,
        "lat": CITY_1_LAT,
        "lon": CITY_1_LON,
        "country": "FR",
        "admin": "Rhône-Alpes",
        "admin2": "74",
    }
)

CITY_2_NAME = "Auch"
CITY_2_LAT = 43.64528
CITY_2_LON = 0.58861
CITY_2 = Place(
    {
        "name": CITY_2_NAME,
        "lat": CITY_2_LAT,
        "lon": CITY_2_LON,
        "country": "FR",
        "admin": "Midi-Pyrénées",
        "admin2": "32",
    }
)

CITY_3_NAME = "Auchel"
CITY_3_LAT = 50.50833
CITY_3_LON = 2.47361
CITY_3 = Place(
    {
        "name": CITY_3_NAME,
        "lat": CITY_3_LAT,
        "lon": CITY_3_LON,
        "country": "FR",
        "admin": "Nord-Pas-de-Calais",
        "admin2": "62",
    }
)


@fixture
def client_single() -> Generator[MagicMock]:
    """Mock a successful client returning one place."""
    with patch(
        "homeassistant.components.meteo_france.config_flow.MeteoFranceClient",
        update=False,
    ) as service_mock:
        service_mock.return_value.search_places.return_value = [CITY_1]
        yield service_mock


@fixture
def client_multiple() -> Generator[MagicMock]:
    """Mock a successful client returning multiple places."""
    with patch(
        "homeassistant.components.meteo_france.config_flow.MeteoFranceClient",
        update=False,
    ) as service_mock:
        service_mock.return_value.search_places.return_value = [CITY_2, CITY_3]
        yield service_mock


@fixture
def client_empty() -> Generator[MagicMock]:
    """Mock a successful client returning no places."""
    with patch(
        "homeassistant.components.meteo_france.config_flow.MeteoFranceClient",
        update=False,
    ) as service_mock:
        service_mock.return_value.search_places.return_value = []
        yield service_mock


@fixture
def mock_setup() -> Generator[None]:
    """Prevent setup."""
    with patch(
        "homeassistant.components.meteo_france.async_setup_entry",
        return_value=True,
    ):
        yield
