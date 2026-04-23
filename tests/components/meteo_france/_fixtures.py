"""Tryke fixtures for Meteo-France config_flow tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from meteofrance_api.model import Place
from tryke import fixture


CITY_1_POSTAL = "74220"
CITY_1_NAME = "La Clusaz"
CITY_1_LAT = 45.90417
CITY_1_LON = 6.42306
CITY_1_COUNTRY = "FR"
CITY_1_ADMIN = "Rhône-Alpes"
CITY_1_ADMIN2 = "74"
CITY_1 = Place(
    {
        "name": CITY_1_NAME,
        "lat": CITY_1_LAT,
        "lon": CITY_1_LON,
        "country": CITY_1_COUNTRY,
        "admin": CITY_1_ADMIN,
        "admin2": CITY_1_ADMIN2,
    }
)

CITY_2_NAME = "Auch"
CITY_2_LAT = 43.64528
CITY_2_LON = 0.58861
CITY_2_COUNTRY = "FR"
CITY_2_ADMIN = "Midi-Pyrénées"
CITY_2_ADMIN2 = "32"
CITY_2 = Place(
    {
        "name": CITY_2_NAME,
        "lat": CITY_2_LAT,
        "lon": CITY_2_LON,
        "country": CITY_2_COUNTRY,
        "admin": CITY_2_ADMIN,
        "admin2": CITY_2_ADMIN2,
    }
)

CITY_3_NAME = "Auchel"
CITY_3_LAT = 50.50833
CITY_3_LON = 2.47361
CITY_3_COUNTRY = "FR"
CITY_3_ADMIN = "Nord-Pas-de-Calais"
CITY_3_ADMIN2 = "62"
CITY_3 = Place(
    {
        "name": CITY_3_NAME,
        "lat": CITY_3_LAT,
        "lon": CITY_3_LON,
        "country": CITY_3_COUNTRY,
        "admin": CITY_3_ADMIN,
        "admin2": CITY_3_ADMIN2,
    }
)


@fixture
def client_single() -> Generator[MagicMock]:
    """Mock a successful client with a single city."""
    with patch(
        "homeassistant.components.meteo_france.config_flow.MeteoFranceClient",
        update=False,
    ) as service_mock:
        service_mock.return_value.search_places.return_value = [CITY_1]
        yield service_mock


@fixture
def client_multiple() -> Generator[MagicMock]:
    """Mock a successful client with multiple cities."""
    with patch(
        "homeassistant.components.meteo_france.config_flow.MeteoFranceClient",
        update=False,
    ) as service_mock:
        service_mock.return_value.search_places.return_value = [CITY_2, CITY_3]
        yield service_mock


@fixture
def client_empty() -> Generator[MagicMock]:
    """Mock a successful client with no cities."""
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
