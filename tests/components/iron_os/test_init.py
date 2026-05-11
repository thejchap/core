"""Test init of IronOS integration."""

from datetime import timedelta
from unittest.mock import AsyncMock, MagicMock

from freezegun.api import FrozenDateTimeFactory
from pynecil import CommunicationError, DeviceInfoResponse
from tryke import Depends, expect, fixture, test

from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNKNOWN
from homeassistant.core import HomeAssistant
import homeassistant.helpers.device_registry as dr
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH

from ._fixtures import (
    DEFAULT_NAME,
    ble_device as ble_device_fixture,
    config_entry as config_entry_fixture,
    mock_pynecil as mock_pynecil_fixture,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import entity_registry_enabled_by_default


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def setup_and_unload(
    hass: HomeAssistant = Depends(_trigger_executor),
    _mock_pynecil: AsyncMock = Depends(mock_pynecil_fixture),
    _ble_device: MagicMock = Depends(ble_device_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test integration setup and unload."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test.skip("entity_id slugs require translation injection for pinecil_boost_temperature")
async def settings_exception(
    hass: HomeAssistant = Depends(_trigger_executor),
    _enabled: object = Depends(entity_registry_enabled_by_default),
    _ble_device: MagicMock = Depends(ble_device_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    mock_pynecil: AsyncMock = Depends(mock_pynecil_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test skipping of settings on exception."""
    mock_pynecil.get_settings.side_effect = CommunicationError

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    freezer.tick(timedelta(seconds=3))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    state = hass.states.get("number.pinecil_boost_temperature")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_UNKNOWN)


@test.skip("entity_id slugs require translation injection for pinecil select entities")
async def v223_entities_not_loaded(
    hass: HomeAssistant = Depends(_trigger_executor),
    _enabled: object = Depends(entity_registry_enabled_by_default),
    _ble_device: MagicMock = Depends(ble_device_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    mock_pynecil: AsyncMock = Depends(mock_pynecil_fixture),
) -> None:
    """Test the new entities in IronOS v2.23 are not loaded on smaller versions."""
    mock_pynecil.get_device_info.return_value = DeviceInfoResponse(
        build="v2.22",
        device_id="c0ffeeC0",
        address="c0:ff:ee:c0:ff:ee",
        device_sn="0000c0ffeec0ffee",
        name=DEFAULT_NAME,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(hass.states.get("number.pinecil_hall_sensor_sleep_timeout")).to_be(None)
    expect(hass.states.get("select.pinecil_soldering_tip_type")).to_be(None)
    state = hass.states.get("select.pinecil_power_delivery_3_1_epr")
    expect(state is not None).to_be(True)

    expect(len(state.attributes["options"])).to_equal(2)


@test
async def device_info_update(
    hass: HomeAssistant = Depends(_trigger_executor),
    _ble_device: MagicMock = Depends(ble_device_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    mock_pynecil: AsyncMock = Depends(mock_pynecil_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test device info gets updated."""
    mock_pynecil.get_device_info.return_value = DeviceInfoResponse()
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    device = device_registry.async_get_device(
        connections={(CONNECTION_BLUETOOTH, config_entry.unique_id)}
    )
    expect(device is not None).to_be(True)
    expect(device.sw_version).to_be(None)
    expect(device.serial_number).to_be(None)

    mock_pynecil.get_device_info.return_value = DeviceInfoResponse(
        build="v2.22",
        device_id="c0ffeeC0",
        address="c0:ff:ee:c0:ff:ee",
        device_sn="0000c0ffeec0ffee",
        name=DEFAULT_NAME,
    )

    freezer.tick(timedelta(seconds=60))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    device = device_registry.async_get_device(
        connections={(CONNECTION_BLUETOOTH, config_entry.unique_id)}
    )
    expect(device is not None).to_be(True)
    expect(device.sw_version).to_equal("v2.22")
    expect(device.serial_number).to_equal("0000c0ffeec0ffee (ID:c0ffeeC0)")
