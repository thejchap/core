"""Tryke fixtures for the Meteoclimatic integration."""

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from tryke import fixture


TEST_STATION_CODE = "ESCAT4300000043206B"
TEST_STATION_NAME = "Reus (Tarragona)"


@fixture
def patch_requests() -> Generator[None]:
    """Stub out services that makes requests."""
    with patch(
        "homeassistant.components.meteoclimatic.coordinator.MeteoclimaticClient"
    ):
        yield


@fixture
def client() -> Generator[MagicMock]:
    """Mock a successful client."""
    with patch(
        "homeassistant.components.meteoclimatic.config_flow.MeteoclimaticClient",
        update=False,
    ) as service_mock:
        service_mock.return_value.get_data.return_value = {
            "station_code": TEST_STATION_CODE
        }
        weather = service_mock.return_value.weather_at_station.return_value
        weather.station.name = TEST_STATION_NAME
        yield service_mock


@fixture
def mock_setup() -> Generator[None]:
    """Prevent setup."""
    with patch(
        "homeassistant.components.meteoclimatic.async_setup_entry",
        return_value=True,
    ):
        yield
