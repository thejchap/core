"""Test Green Planet Energy setup."""

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import init_integration as init_integration_fixture

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Tryke discovery anchor."""


@test
async def setup_entry(
    _trigger: None = Depends(_trigger_executor),
    init_integration: MockConfigEntry = Depends(init_integration_fixture),
) -> None:
    """Test setting up config entry."""
    expect(init_integration.state).to_be(ConfigEntryState.LOADED)


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    init_integration: MockConfigEntry = Depends(init_integration_fixture),
) -> None:
    """Test unloading config entry."""
    expect(init_integration.state).to_be(ConfigEntryState.LOADED)

    result = await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()

    expect(result).to_be(True)
    expect(init_integration.state).to_be(ConfigEntryState.NOT_LOADED)
