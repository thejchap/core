"""Test init of israel_rail integration."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import init_integration
from ._fixtures import mock_config_entry, mock_israelrail

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture."""
    return hass


@test
async def invalid_config(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
    mock_israelrail: AsyncMock = Depends(mock_israelrail),
) -> None:
    """Ensure nothing is created when config is wrong."""
    mock_israelrail.query.side_effect = Exception("error")
    await init_integration(hass, mock_config_entry)
    expect(bool(hass.states.async_entity_ids("sensor"))).to_be(False)
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
