"""Tryke fixtures for Tankerkoenig integration tests."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import fixture

from homeassistant.components.tankerkoenig import DOMAIN
from homeassistant.const import CONF_SHOW_ON_MAP

from .const import CONFIG_DATA, NEARBY_STATIONS, PRICES, STATION

from tests.common import MockConfigEntry


@fixture
def tankerkoenig() -> Generator[AsyncMock]:
    """Mock the aiotankerkoenig client."""
    with (
        patch(
            "homeassistant.components.tankerkoenig.coordinator.Tankerkoenig",
            autospec=True,
        ) as mock_tankerkoenig,
        patch(
            "homeassistant.components.tankerkoenig.config_flow.Tankerkoenig",
            new=mock_tankerkoenig,
        ),
    ):
        mock = mock_tankerkoenig.return_value
        mock.station_details.return_value = STATION
        mock.prices.return_value = PRICES
        mock.nearby_stations.return_value = NEARBY_STATIONS
        yield mock


@fixture
def config_entry() -> MockConfigEntry:
    """Return a MockConfigEntry for testing."""
    return MockConfigEntry(
        domain=DOMAIN,
        title="Mock Title",
        unique_id="51.0_13.0",
        entry_id="8036b4412f2fae6bb9dbab7fe8e37f87",
        options={
            CONF_SHOW_ON_MAP: True,
        },
        data=CONFIG_DATA,
    )
