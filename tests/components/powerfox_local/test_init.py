"""Test the Powerfox Local init module."""

from unittest.mock import AsyncMock

from powerfox import PowerfoxAuthenticationError, PowerfoxConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_config_entry, mock_powerfox_local_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def load_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_powerfox_local_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def config_entry_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test config entry not ready on connection error."""
    client.value.side_effect = PowerfoxConnectionError
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_entry_exception(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_local_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test ConfigEntryNotReady when API raises an exception during entry setup."""
    config_entry.add_to_hass(hass)
    client.value.side_effect = PowerfoxAuthenticationError

    await hass.config_entries.async_setup(config_entry.entry_id)
    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["step_id"]).to_equal("reauth_confirm")
