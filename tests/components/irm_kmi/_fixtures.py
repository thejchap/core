"""Tryke fixtures for the irm_kmi integration."""

from collections.abc import Generator
from unittest.mock import patch

from irm_kmi_api import IrmKmiApiError
from tryke import fixture

from homeassistant.components.irm_kmi.const import DOMAIN
from homeassistant.const import (
    ATTR_LATITUDE,
    ATTR_LONGITUDE,
    CONF_LOCATION,
    CONF_UNIQUE_ID,
)

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Home",
        domain=DOMAIN,
        data={
            CONF_LOCATION: {ATTR_LATITUDE: 50.84, ATTR_LONGITUDE: 4.35},
            CONF_UNIQUE_ID: "city country",
        },
        unique_id="50.84-4.35",
    )


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch("homeassistant.components.irm_kmi.async_setup_entry", return_value=True):
        yield


@fixture
def mock_get_forecast_in_benelux() -> Generator[None]:
    """Mock get_forecasts_coord() so it returns a valid Benelux response."""
    with patch(
        "homeassistant.components.irm_kmi.config_flow.IrmKmiApiClient.get_forecasts_coord",
        return_value={"cityName": "Brussels", "country": "BE"},
    ):
        yield


@fixture
def mock_get_forecast_out_benelux_then_in_belgium() -> Generator[None]:
    """Mock get_forecasts_coord() to return outside-then-inside-Benelux."""
    with patch(
        "homeassistant.components.irm_kmi.config_flow.IrmKmiApiClient.get_forecasts_coord",
        side_effect=[
            {"cityName": "Outside the Benelux (Brussels)", "country": "BE"},
            {"cityName": "Brussels", "country": "BE"},
        ],
    ):
        yield


@fixture
def mock_get_forecast_api_error() -> Generator[None]:
    """Mock get_forecasts_coord() so it raises an error."""
    with patch(
        "homeassistant.components.irm_kmi.config_flow.IrmKmiApiClient.get_forecasts_coord",
        side_effect=IrmKmiApiError,
    ):
        yield
