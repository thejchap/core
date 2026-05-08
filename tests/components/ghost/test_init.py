"""Tests for Ghost integration setup."""

from unittest.mock import AsyncMock

from aioghost.exceptions import GhostAuthError, GhostConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import (
    mock_config_entry as mock_config_entry_fixture,
    mock_ghost_api as mock_ghost_api_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Tryke discovery anchor."""


@test.cases(
    test.case(
        "auth_error",
        side_effect=GhostAuthError("Invalid API key"),
        expected_state=ConfigEntryState.SETUP_ERROR,
    ),
    test.case(
        "connection_error",
        side_effect=GhostConnectionError("Connection failed"),
        expected_state=ConfigEntryState.SETUP_RETRY,
    ),
)
async def setup_entry_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_ghost_api: AsyncMock = Depends(mock_ghost_api_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
    *,
    side_effect: Exception,
    expected_state: ConfigEntryState,
) -> None:
    """Test setup errors."""
    mock_ghost_api.get_site.side_effect = side_effect

    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(expected_state)


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_ghost_api: AsyncMock = Depends(mock_ghost_api_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fixture),
) -> None:
    """Test unloading config entry."""
    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
