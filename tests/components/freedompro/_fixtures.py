"""Tryke fixtures for the freedompro integration."""

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from tryke import Depends, fixture

from homeassistant.components.freedompro.const import DOMAIN
from homeassistant.core import HomeAssistant

from .const import DEVICES, DEVICES_STATE

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.freedompro.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def mock_freedompro() -> Generator[None]:
    """Mock freedompro get_list and get_states."""
    with (
        patch(
            "homeassistant.components.freedompro.coordinator.get_list",
            return_value={
                "state": True,
                "devices": DEVICES,
            },
        ),
        patch(
            "homeassistant.components.freedompro.coordinator.get_states",
            return_value=DEVICES_STATE,
        ),
    ):
        yield


@fixture
async def init_integration(
    hass: HomeAssistant = Depends(hass_fixture),
    _freedompro: None = Depends(mock_freedompro),
) -> MockConfigEntry:
    """Set up the Freedompro integration in Home Assistant."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="Feedompro",
        unique_id="0123456",
        data={
            "api_key": "gdhsksjdhcncjdkdjndjdkdmndjdjdkd",
        },
    )

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    return entry
