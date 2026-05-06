"""Tests for the Actron Air coordinator."""

from unittest.mock import AsyncMock, patch

from actron_neo_api import ActronAirAPIError, ActronAirAuthError
from tryke import Depends, expect, fixture, test

from homeassistant.components.actron_air.coordinator import SCAN_INTERVAL
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_actron_api, mock_config_entry

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import freezer as freezer_fixture, hass as hass_fixture


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def coordinator_update_auth_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: AsyncMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test coordinator handles auth error during update."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    mock_actron_api.update_status.side_effect = ActronAirAuthError("Auth expired")

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(len(hass.config_entries.flow.async_progress())).to_equal(1)


@test
async def coordinator_update_api_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: AsyncMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test coordinator handles API error during update."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    mock_actron_api.update_status.side_effect = ActronAirAPIError("API error")

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    coordinator = list(mock_config_entry.runtime_data.system_coordinators.values())[0]
    expect(coordinator.last_update_success).to_be(False)


@test
async def coordinator_update_status_none(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: AsyncMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    freezer=Depends(freezer_fixture),
) -> None:
    """Test coordinator handles get_status returning None."""
    with patch("homeassistant.components.actron_air.PLATFORMS", [Platform.CLIMATE]):
        await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    mock_actron_api.state_manager.get_status.return_value = None

    freezer.tick(SCAN_INTERVAL)
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    coordinator = list(mock_config_entry.runtime_data.system_coordinators.values())[0]
    expect(coordinator.last_update_success).to_be(False)
