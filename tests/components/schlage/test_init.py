"""Tests for the Schlage integration."""

from __future__ import annotations

from unittest.mock import Mock, patch

from pycognito.exceptions import WarrantException
from pyschlage.exceptions import Error, NotAuthorizedError
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import MockSchlageConfigEntry
from ._fixtures import (
    mock_config_entry as mock_config_entry_fx,
    mock_pyschlage_auth as mock_pyschlage_auth_fx,
    mock_schlage as mock_schlage_fx,
)

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def auth_failed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockSchlageConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test failed auth on setup."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "pyschlage.Auth",
        side_effect=WarrantException,
    ) as mock_auth:
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()

        expect(mock_auth.call_count).to_equal(1)
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_ERROR)


@test
async def update_data_fails(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockSchlageConfigEntry = Depends(mock_config_entry_fx),
    _mock_pyschlage_auth: Mock = Depends(mock_pyschlage_auth_fx),
    mock_schlage: Mock = Depends(mock_schlage_fx),
) -> None:
    """Test that we properly handle API errors."""
    mock_schlage.locks.side_effect = Error
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_schlage.locks.call_count).to_equal(1)
    expect(mock_config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def update_data_auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockSchlageConfigEntry = Depends(mock_config_entry_fx),
    _mock_pyschlage_auth: Mock = Depends(mock_pyschlage_auth_fx),
    mock_schlage: Mock = Depends(mock_schlage_fx),
) -> None:
    """Test that we properly handle auth errors."""
    mock_schlage.locks.side_effect = NotAuthorizedError
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_schlage.locks.call_count).to_equal(1)


@test
async def load_unload_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockSchlageConfigEntry = Depends(mock_config_entry_fx),
    _mock_pyschlage_auth: Mock = Depends(mock_pyschlage_auth_fx),
    _mock_schlage: Mock = Depends(mock_schlage_fx),
) -> None:
    """Test the Schlage configuration entry loading/unloading."""
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(mock_config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    expect(mock_config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("requires update_data_get_logs_auth_error helpers")
async def update_data_get_logs_auth_error() -> None:
    """Stub for test_update_data_get_logs_auth_error (port deferred)."""


@test.skip("syrupy snapshot")
async def lock_device_registry() -> None:
    """Stub for test_lock_device_registry (port deferred)."""


@test.skip("requires mock_lock + freezer chain")
async def auto_add_device() -> None:
    """Stub for test_auto_add_device (port deferred)."""


@test.skip("requires mock_lock + freezer chain")
async def auto_remove_device() -> None:
    """Stub for test_auto_remove_device (port deferred)."""
