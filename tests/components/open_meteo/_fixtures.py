"""Tryke fixtures for the Open-Meteo integration tests."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import MagicMock, patch

from open_meteo import Forecast
from tryke import fixture

from homeassistant.components.open_meteo.const import DOMAIN
from homeassistant.const import CONF_ZONE

from tests.common import MockConfigEntry, load_fixture


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Home",
        domain=DOMAIN,
        data={CONF_ZONE: "zone.home"},
        unique_id="zone.home",
    )


@fixture
def mock_setup_entry() -> Generator[None]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.open_meteo.async_setup_entry", return_value=True
    ):
        yield


@fixture
def mock_open_meteo() -> Generator[MagicMock]:
    """Return a mocked Open-Meteo client."""
    forecast = Forecast.from_json(load_fixture("forecast.json", DOMAIN))
    with patch(
        "homeassistant.components.open_meteo.coordinator.OpenMeteo", autospec=True
    ) as open_meteo_mock:
        open_meteo = open_meteo_mock.return_value
        open_meteo.forecast.return_value = forecast
        yield open_meteo
