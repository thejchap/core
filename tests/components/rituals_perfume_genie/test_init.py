"""Tests for the Rituals Perfume Genie integration."""

from __future__ import annotations

from unittest.mock import AsyncMock

import aiohttp
from tryke import Depends, expect, fixture, test

from homeassistant.components.rituals_perfume_genie.const import ACCOUNT_HASH
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_rituals_account as mock_rituals_account_fx,
    old_mock_config_entry as old_mock_config_entry_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def migration_v1_to_v2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_rituals_account: AsyncMock = Depends(mock_rituals_account_fx),
    old_mock_config_entry: MockConfigEntry = Depends(old_mock_config_entry_fx),
) -> None:
    """Test migration from V1 (account_hash) to V2 (credentials)."""
    old_mock_config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(old_mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(old_mock_config_entry.version).to_equal(2)
    expect(ACCOUNT_HASH not in old_mock_config_entry.data).to_be(True)
    expect(old_mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)
    expect(len(hass.config_entries.flow.async_progress())).to_equal(1)


@test
async def config_entry_not_ready(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_rituals_account: AsyncMock = Depends(mock_rituals_account_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test the Rituals configuration entry setup if connection to Rituals is missing."""
    mock_config_entry.add_to_hass(hass)
    mock_rituals_account.get_devices.side_effect = aiohttp.ClientError

    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test.skip("requires init_integration helper from common.py")
async def config_entry_unload() -> None:
    """Stub for test_config_entry_unload (port deferred)."""


@test.skip("requires init_integration helper from common.py")
async def entity_id_migration() -> None:
    """Stub for test_entity_id_migration (port deferred)."""
