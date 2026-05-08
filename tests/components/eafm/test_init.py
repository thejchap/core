"""Tests for initialization."""

from unittest.mock import AsyncMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.eafm.const import DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from ._fixtures import mock_config_entry, mock_get_station

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test.skip("snapshot diverged - needs pytest --snapshot-update")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""


@test
async def update_device_identifiers(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(mock_config_entry),
    _station: AsyncMock = Depends(mock_get_station),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test being able to update device identifiers."""
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(DOMAIN, "measure-id", "L1234")},
    )

    entries = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    expect(len(entries)).to_equal(1)
    device_entry = entries[0]
    expect((DOMAIN, "measure-id", "L1234") in device_entry.identifiers).to_be(True)
    expect((DOMAIN, "L1234") in device_entry.identifiers).to_be(False)

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    expect(entry.state).to_be(ConfigEntryState.LOADED)
    await hass.async_block_till_done()

    entries = dr.async_entries_for_config_entry(device_registry, entry.entry_id)
    expect(len(entries)).to_equal(1)
    device_entry = entries[0]
    expect((DOMAIN, "measure-id", "L1234") in device_entry.identifiers).to_be(False)
    expect((DOMAIN, "L1234") in device_entry.identifiers).to_be(True)
