"""Tests for the IRM KMI integration."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.irm_kmi.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_config_entry,
    mock_exception_irm_kmi_api,
    mock_irm_kmi_api,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def load_unload_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_irm_kmi_api: MagicMock = Depends(mock_irm_kmi_api),
) -> None:
    """Test the IRM KMI configuration entry loading/unloading."""
    mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(bool(hass.data.get(DOMAIN))).to_be(False)
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def config_entry_not_ready(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_exception_irm_kmi_api: MagicMock = Depends(mock_exception_irm_kmi_api),
) -> None:
    """Test the IRM KMI configuration entry not ready."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_exception_irm_kmi_api.refresh_forecasts_coord.call_count).to_equal(1)
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
