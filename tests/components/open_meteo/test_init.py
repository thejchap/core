"""Tests for the Open-Meteo integration."""

from unittest.mock import AsyncMock, MagicMock, patch

from open_meteo import OpenMeteoConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.open_meteo.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ZONE
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.components.open_meteo._fixtures import mock_config_entry, mock_open_meteo
from tests.hass_fixtures import LogCapture, caplog, hass, mock_network


@fixture
def _trigger_executor() -> int:
    """Opt the module into Tryke's HookExecutor path."""
    return 0


@test
async def load_unload_config_entry(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    _mock_open_meteo: AsyncMock = Depends(mock_open_meteo),
) -> None:
    """Test the Open-Meteo configuration entry loading/unloading."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state is ConfigEntryState.LOADED).to_be(True)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(bool(hass.data.get(DOMAIN))).to_be(False)
    expect(mock_config_entry.state is ConfigEntryState.NOT_LOADED).to_be(True)


@test
async def config_entry_not_ready(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the Open-Meteo configuration entry not ready."""
    with patch(
        "homeassistant.components.open_meteo.coordinator.OpenMeteo.forecast",
        side_effect=OpenMeteoConnectionError,
    ) as mock_forecast:
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        expect(mock_forecast.call_count).to_equal(1)
        expect(mock_config_entry.state is ConfigEntryState.SETUP_RETRY).to_be(True)


@test
async def config_entry_zone_removed(
    hass: HomeAssistant = Depends(hass),
    _mock_network: None = Depends(mock_network),
    caplog: LogCapture = Depends(caplog),
) -> None:
    """Test the Open-Meteo configuration entry not ready when zone is missing."""
    mock_config_entry = MockConfigEntry(
        title="My Castle",
        domain=DOMAIN,
        data={CONF_ZONE: "zone.castle"},
        unique_id="zone.castle",
    )
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state is ConfigEntryState.SETUP_RETRY).to_be(True)
    expect("Zone 'zone.castle' not found" in caplog.text).to_be(True)
