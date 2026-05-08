"""Tests for the Pure Energie integration."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

from gridnet import GridNetConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_pure_energie as mock_pure_energie_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_pure_energie: AsyncMock = Depends(mock_pure_energie_fx),
) -> None:
    """Test the Pure Energie configuration entry loading/unloading."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(mock_config_entry.unique_id).to_equal("unique_thingy")
    expect(len(mock_pure_energie.mock_calls)).to_equal(3)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def config_entry_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test the Pure Energie configuration entry not ready."""
    with patch(
        "homeassistant.components.pure_energie.coordinator.GridNet._request",
        side_effect=GridNetConnectionError,
    ):
        mock_config_entry.add_to_hass(hass)
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)
