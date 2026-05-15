"""Test Snooz configuration."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from . import SnoozFixture
from ._fixtures import mock_connected_snooz as mock_connected_snooz_fixture

from tests.hass_fixtures import (
    enable_bluetooth,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def removing_entry_cleans_up_connections(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_connected_snooz: SnoozFixture = Depends(mock_connected_snooz_fixture),
) -> None:
    """Tests setup and removal of a config entry, ensuring connections are cleaned up."""
    await hass.config_entries.async_remove(mock_connected_snooz.entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_connected_snooz.device.is_connected).to_be(False)


@test
async def reloading_entry_cleans_up_connections(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_connected_snooz: SnoozFixture = Depends(mock_connected_snooz_fixture),
) -> None:
    """Test reloading an entry disconnects any existing connections."""
    await hass.config_entries.async_reload(mock_connected_snooz.entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_connected_snooz.device.is_connected).to_be(False)
