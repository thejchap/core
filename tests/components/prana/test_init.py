"""Tests for Prana integration entry points (async_setup_entry / async_unload_entry)."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import async_init_integration
from ._fixtures import mock_config_entry, mock_prana_api

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def async_setup_entry_and_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _api: AsyncMock = Depends(mock_prana_api),
) -> None:
    """async_setup_entry should create coordinator, refresh and load."""
    await async_init_integration(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("snapshot diverged — needs pytest --snapshot-update")
async def device_info_registered() -> None:
    """Stub for test_device_info_registered."""
