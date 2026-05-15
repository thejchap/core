"""Tests for bosch alarm integration init."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from tests.common import MockConfigEntry
from tests.components.bosch_alarm import setup_integration
from tests.components.bosch_alarm._fixtures import (
    disable_platform_only,
    mock_config_entry_solution_3000,
    mock_panel_solution_3000,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _disable_platforms: None = Depends(disable_platform_only),
) -> None:
    """Anchor for tryke fixture resolution."""


@test.cases(
    test.case("permission_error", exception=PermissionError()),
)
async def incorrect_auth(
    *,
    exception: Exception,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_panel: AsyncMock = Depends(mock_panel_solution_3000),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_solution_3000),
) -> None:
    """Test errors with incorrect auth."""
    mock_panel.connect.side_effect = exception
    await setup_integration(hass, mock_config_entry)
    expect(mock_config_entry.state is ConfigEntryState.SETUP_ERROR).to_be(True)


@test.cases(
    test.case("timeout_error", exception=TimeoutError()),
)
async def connection_error(
    *,
    exception: Exception,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_panel: AsyncMock = Depends(mock_panel_solution_3000),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_solution_3000),
) -> None:
    """Test errors with incorrect auth."""
    mock_panel.connect.side_effect = exception
    await setup_integration(hass, mock_config_entry)
    expect(mock_config_entry.state is ConfigEntryState.SETUP_RETRY).to_be(True)
