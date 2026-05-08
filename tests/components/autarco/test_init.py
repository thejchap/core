"""Test the Autarco init module."""

from unittest.mock import AsyncMock

from autarco import AutarcoAuthenticationError, AutarcoConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_autarco_client, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke to fully resolve hass."""
    return hass


@test
async def load_unload_entry(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _client: AsyncMock = Depends(mock_autarco_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test load and unload entry."""
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_remove(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def config_entry_not_ready(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_autarco_client: AsyncMock = Depends(mock_autarco_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the Autarco configuration entry not ready."""
    mock_autarco_client.get_account.side_effect = AutarcoConnectionError
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def setup_entry_exception(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_autarco_client: AsyncMock = Depends(mock_autarco_client),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test ConfigEntryNotReady when API raises an exception during entry setup."""
    mock_config_entry.add_to_hass(hass)
    mock_autarco_client.get_site.side_effect = AutarcoAuthenticationError

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect(flows[0]["step_id"]).to_equal("reauth_confirm")
