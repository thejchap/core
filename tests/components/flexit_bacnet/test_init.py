"""Tests for the Flexit Nordic (BACnet) __init__."""

from unittest.mock import AsyncMock

from flexit_bacnet import DecodingError
from tryke import Depends, expect, fixture, test

from homeassistant.components.flexit_bacnet.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from . import setup_with_selected_platforms
from ._fixtures import (
    mock_config_entry as mock_config_entry_fixture,
    mock_flexit_bacnet as mock_flexit_bacnet_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Tryke discovery anchor."""


@test
async def loading_and_unloading_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    _mock_flexit_bacnet: AsyncMock = Depends(mock_flexit_bacnet_fixture),
) -> None:
    """Test loading and unloading a config entry."""
    await setup_with_selected_platforms(hass, mock_config_entry, [Platform.CLIMATE])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(mock_config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def failed_initialization(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    mock_flexit_bacnet: AsyncMock = Depends(mock_flexit_bacnet_fixture),
) -> None:
    """Test failed initialization."""
    mock_flexit_bacnet.update.side_effect = DecodingError
    mock_config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(mock_config_entry.entry_id)).to_be(False)
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
