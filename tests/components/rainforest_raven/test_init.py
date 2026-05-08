"""Tests for the Rainforest RAVEn component initialisation."""

from __future__ import annotations

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from aioraven.device import RAVEnConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.rainforest_raven.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant

from . import create_mock_device, create_mock_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def mock_device_fx() -> Generator[AsyncMock]:
    """Mock the RAVEn device used by both config_flow and coordinator."""
    device = create_mock_device()
    with (
        patch(
            "homeassistant.components.rainforest_raven.config_flow.RAVEnSerialDevice",
            return_value=device,
        ),
        patch(
            "homeassistant.components.rainforest_raven.coordinator.RAVEnSerialDevice",
            return_value=device,
        ),
    ):
        yield device


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def load_unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_device: AsyncMock = Depends(mock_device_fx),
) -> None:
    """Test load and unload."""
    entry = create_mock_entry()
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(entry.state).to_be(ConfigEntryState.LOADED)

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("syrupy snapshot (device_registry)")
async def device_registry() -> None:
    """Stub for test_device_registry (port deferred)."""


@test
async def synchronize_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: AsyncMock = Depends(mock_device_fx),
) -> None:
    """Test handling of an error parsing or reading raw device data."""
    entry = create_mock_entry()
    entry.add_to_hass(hass)

    mock_device.synchronize.side_effect = RAVEnConnectionError

    await hass.config_entries.async_setup(entry.entry_id)

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def get_network_info_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mock_device: AsyncMock = Depends(mock_device_fx),
) -> None:
    """Test handling of a device error during initialization."""
    entry = create_mock_entry()
    entry.add_to_hass(hass)

    mock_device.get_network_info.side_effect = RAVEnConnectionError
    await hass.config_entries.async_setup(entry.entry_id)

    expect(entry.state).to_be(ConfigEntryState.SETUP_RETRY)
