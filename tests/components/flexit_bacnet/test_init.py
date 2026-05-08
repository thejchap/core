"""Tests for the Flexit Nordic (BACnet) __init__."""

from unittest.mock import AsyncMock

from flexit_bacnet import DecodingError
from tryke import Depends, expect, fixture, test

from homeassistant.components.flexit_bacnet.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from . import setup_with_selected_platforms
from ._fixtures import mock_config_entry, mock_flexit_bacnet

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def loading_and_unloading_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _flexit: AsyncMock = Depends(mock_flexit_bacnet),
) -> None:
    """Test loading and unloading a config entry."""
    await setup_with_selected_platforms(hass, entry, [Platform.CLIMATE])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def failed_initialization(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    flexit: AsyncMock = Depends(mock_flexit_bacnet),
) -> None:
    """Test failed initialization."""
    flexit.update.side_effect = DecodingError
    entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(False)
    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
