"""Tests for the Actron Air integration setup."""

from unittest.mock import AsyncMock

from actron_neo_api import ActronAirAPIError, ActronAirAuthError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import setup_integration
from ._fixtures import mock_actron_api, mock_config_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def setup_entry_auth_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: AsyncMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setup entry raises ConfigEntryAuthFailed on auth error."""
    mock_actron_api.get_ac_systems.side_effect = ActronAirAuthError("Auth failed")

    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def setup_entry_api_error(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_actron_api: AsyncMock = Depends(mock_actron_api),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test setup entry raises ConfigEntryNotReady on API error."""
    mock_actron_api.get_ac_systems.side_effect = ActronAirAPIError("API failed")

    await setup_integration(hass, mock_config_entry)

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
