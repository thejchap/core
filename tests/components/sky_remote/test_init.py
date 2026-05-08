"""Tests for the Sky Remote component."""

from unittest.mock import AsyncMock, MagicMock

from skyboxremote import SkyBoxConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.sky_remote.const import DEFAULT_PORT, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from . import setup_mock_entry
from ._fixtures import mock_config_entry, mock_remote_control

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level anchor fixture."""


@test
async def setup_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    remote_control: MagicMock = Depends(mock_remote_control),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test successful setup of entry."""
    await setup_mock_entry(hass, config_entry)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    remote_control.assert_called_once_with("example.com", DEFAULT_PORT)
    device_entry = device_registry.async_get_device(
        identifiers={(DOMAIN, config_entry.entry_id)}
    )
    expect(device_entry is not None).to_be(True)
    expect(device_entry.name).to_equal("example.com")


@test
async def setup_unconnectable_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    remote_control: MagicMock = Depends(mock_remote_control),
) -> None:
    """Test unsuccessful setup of entry."""
    remote_control._instance_mock.check_connectable = AsyncMock(
        side_effect=SkyBoxConnectionError()
    )

    await setup_mock_entry(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.SETUP_RETRY)


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _remote: MagicMock = Depends(mock_remote_control),
) -> None:
    """Test unload an entry."""
    await setup_mock_entry(hass, config_entry)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(await hass.config_entries.async_unload(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)
