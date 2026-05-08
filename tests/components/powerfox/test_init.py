"""Test the Powerfox init module."""

from unittest.mock import AsyncMock

from powerfox import PowerfoxAuthenticationError, PowerfoxConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_config_entry, mock_powerfox_client

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def load_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_powerfox_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_remove(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def config_entry_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the Powerfox configuration entry not ready."""
    client.all_devices.side_effect = PowerfoxConnectionError
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.cases(
    test.case("all_devices", method="all_devices"),
    test.case("device", method="device"),
)
async def config_entry_auth_failed(
    method: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_powerfox_client),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test ConfigEntryAuthFailed when authentication fails."""
    getattr(client, method).side_effect = PowerfoxAuthenticationError
    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["step_id"]).to_equal("reauth_confirm")
