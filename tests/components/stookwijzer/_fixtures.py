"""Tryke fixtures for Stookwijzer tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, MagicMock, patch

from tryke import fixture

from homeassistant.components.stookwijzer.const import DOMAIN
from homeassistant.components.stookwijzer.services import Forecast
from homeassistant.const import CONF_LATITUDE, CONF_LOCATION, CONF_LONGITUDE

from tests.common import MockConfigEntry


@fixture
def mock_config_entry() -> MockConfigEntry:
    """Return the default mocked config entry."""
    return MockConfigEntry(
        title="Stookwijzer",
        domain=DOMAIN,
        data={
            CONF_LATITUDE: 200000.1234567890,
            CONF_LONGITUDE: 450000.1234567890,
        },
        version=2,
        entry_id="12345",
    )


@fixture
def mock_v1_config_entry() -> MockConfigEntry:
    """Return the default mocked version 1 config entry."""
    return MockConfigEntry(
        title="Stookwijzer",
        domain=DOMAIN,
        data={
            CONF_LOCATION: {
                CONF_LATITUDE: 1.0,
                CONF_LONGITUDE: 1.1,
            },
        },
        version=1,
        entry_id="12345",
    )


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Mock setting up a config entry."""
    with patch(
        "homeassistant.components.stookwijzer.async_setup_entry", return_value=True
    ) as mock_setup:
        yield mock_setup


@fixture
def mock_stookwijzer() -> Generator[MagicMock]:
    """Return a mocked Stookwijzer client."""
    with (
        patch(
            "homeassistant.components.stookwijzer.Stookwijzer",
            autospec=True,
        ) as stookwijzer_mock,
        patch(
            "homeassistant.components.stookwijzer.coordinator.Stookwijzer",
            new=stookwijzer_mock,
        ),
        patch(
            "homeassistant.components.stookwijzer.config_flow.Stookwijzer",
            new=stookwijzer_mock,
        ),
    ):
        stookwijzer_mock.async_transform_coordinates.return_value = {
            "x": 450000.123456789,
            "y": 200000.123456789,
        }

        client = stookwijzer_mock.return_value
        client.lki = 2
        client.windspeed_ms = 2.5
        client.windspeed_bft = 2
        client.advice = "code_yellow"
        client.async_get_forecast.return_value = (
            Forecast(
                datetime="2025-02-12T17:00:00+01:00",
                advice="code_yellow",
                final=True,
            ),
            Forecast(
                datetime="2025-02-12T23:00:00+01:00",
                advice="code_yellow",
                final=True,
            ),
            Forecast(
                datetime="2025-02-13T05:00:00+01:00",
                advice="code_orange",
                final=False,
            ),
            Forecast(
                datetime="2025-02-13T11:00:00+01:00",
                advice="code_orange",
                final=False,
            ),
        )

        yield stookwijzer_mock
