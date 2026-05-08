"""Tests for the Elgato Key Light integration."""

from unittest.mock import MagicMock

from elgato import ElgatoConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, mock_elgato

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    mock_client: MagicMock = Depends(mock_elgato),
) -> None:
    """Test the Elgato configuration entry loading/unloading."""
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.LOADED)
    expect(len(mock_client.info.mock_calls)).to_equal(1)

    await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def config_entry_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    mock_client: MagicMock = Depends(mock_elgato),
) -> None:
    """Test the Elgato configuration entry not ready."""
    mock_client.state.side_effect = ElgatoConnectionError

    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(len(mock_client.state.mock_calls)).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
