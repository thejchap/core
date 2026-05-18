"""Test the Airthings Wave sensor."""

from copy import deepcopy
from datetime import timedelta
import logging
from typing import Any

from freezegun.api import FrozenDateTimeFactory
from tryke import Depends, expect, fixture, test

from homeassistant.components.airthings_ble.const import (
    DEFAULT_SCAN_INTERVAL,
    DEVICE_MODEL,
    DEVICE_SPECIFIC_SCAN_INTERVAL,
    DOMAIN,
)
from homeassistant.const import STATE_UNKNOWN, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from . import (
    CO2_V1,
    CO2_V2,
    CORENTIUM_HOME_2_DEVICE_INFO,
    CORENTIUM_HOME_2_SERVICE_INFO,
    HUMIDITY_V2,
    TEMPERATURE_V1,
    VOC_V1,
    VOC_V2,
    VOC_V3,
    WAVE_DEVICE_INFO,
    WAVE_ENHANCE_DEVICE_INFO,
    WAVE_ENHANCE_SERVICE_INFO,
    WAVE_SERVICE_INFO,
    AirthingsDevice,
    BluetoothServiceInfoBleak,
    create_device,
    create_entry,
    patch_airthings_ble,
    patch_airthings_device_update,
    patch_async_ble_device_from_address,
    patch_async_discovered_service_info,
)

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.components.bluetooth import inject_bluetooth_service_info
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    enable_bluetooth,
    entity_registry as entity_registry_fixture,
    freezer as freezer_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import (
    entity_registry_enabled_by_default as entity_registry_enabled_by_default_fixture,
)

_LOGGER = logging.getLogger(__name__)


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _bluetooth: None = Depends(enable_bluetooth),
) -> int:
    """Present so tryke builds an async fixture executor for this module."""
    return 0


@test
async def migration_from_v1_to_v3_unique_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Verify that we can migrate from v1 (pre 2023.9.0) to the latest unique id format."""
    entry = create_entry(hass, WAVE_SERVICE_INFO, WAVE_DEVICE_INFO)
    device = create_device(entry, device_registry, WAVE_SERVICE_INFO, WAVE_DEVICE_INFO)

    expect(entry).not_.to_be_none()
    expect(device).not_.to_be_none()

    new_unique_id = f"{WAVE_DEVICE_INFO.address}_temperature"

    sensor = entity_registry.async_get_or_create(
        domain=DOMAIN,
        platform=Platform.SENSOR,
        unique_id=TEMPERATURE_V1.unique_id,
        config_entry=entry,
        device_id=device.id,
    )

    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_be(0)

    inject_bluetooth_service_info(
        hass,
        WAVE_SERVICE_INFO,
    )

    await hass.async_block_till_done()

    with patch_airthings_device_update():
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(len(hass.states.async_all()) > 0).to_be(True)

    expect(entity_registry.async_get(sensor.entity_id).unique_id).to_equal(
        new_unique_id
    )


@test
async def migration_from_v2_to_v3_unique_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Verify that we can migrate from v2 (introduced in 2023.9.0) to the latest unique id format."""
    entry = create_entry(hass, WAVE_SERVICE_INFO, WAVE_DEVICE_INFO)
    device = create_device(entry, device_registry, WAVE_SERVICE_INFO, WAVE_DEVICE_INFO)

    expect(entry).not_.to_be_none()
    expect(device).not_.to_be_none()

    sensor = entity_registry.async_get_or_create(
        domain=DOMAIN,
        platform=Platform.SENSOR,
        unique_id=HUMIDITY_V2.unique_id,
        config_entry=entry,
        device_id=device.id,
    )

    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_be(0)

    inject_bluetooth_service_info(
        hass,
        WAVE_SERVICE_INFO,
    )

    await hass.async_block_till_done()

    with patch_airthings_device_update():
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(len(hass.states.async_all()) > 0).to_be(True)

    # Migration should happen, v2 unique id should be updated to the new format
    new_unique_id = f"{WAVE_DEVICE_INFO.address}_humidity"
    expect(entity_registry.async_get(sensor.entity_id).unique_id).to_equal(
        new_unique_id
    )


@test
async def migration_from_v1_and_v2_to_v3_unique_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test if migration works when we have both v1 (pre 2023.9.0) and v2 (introduced in 2023.9.0) unique ids."""
    entry = create_entry(hass, WAVE_SERVICE_INFO, WAVE_DEVICE_INFO)
    device = create_device(entry, device_registry, WAVE_SERVICE_INFO, WAVE_DEVICE_INFO)

    expect(entry).not_.to_be_none()
    expect(device).not_.to_be_none()

    v2 = entity_registry.async_get_or_create(
        domain=DOMAIN,
        platform=Platform.SENSOR,
        unique_id=CO2_V2.unique_id,
        config_entry=entry,
        device_id=device.id,
    )

    v1 = entity_registry.async_get_or_create(
        domain=DOMAIN,
        platform=Platform.SENSOR,
        unique_id=CO2_V1.unique_id,
        config_entry=entry,
        device_id=device.id,
    )

    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_be(0)

    inject_bluetooth_service_info(
        hass,
        WAVE_SERVICE_INFO,
    )

    await hass.async_block_till_done()

    with patch_airthings_device_update():
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(len(hass.states.async_all()) > 0).to_be(True)

    # Migration should happen, v1 unique id should be updated to the new format
    new_unique_id = f"{WAVE_DEVICE_INFO.address}_co2"
    expect(entity_registry.async_get(v1.entity_id).unique_id).to_equal(new_unique_id)
    expect(entity_registry.async_get(v2.entity_id).unique_id).to_equal(CO2_V2.unique_id)


@test
async def migration_with_all_unique_ids(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test if migration works when we have all unique ids."""
    entry = create_entry(hass, WAVE_SERVICE_INFO, WAVE_DEVICE_INFO)
    device = create_device(entry, device_registry, WAVE_SERVICE_INFO, WAVE_DEVICE_INFO)

    expect(entry).not_.to_be_none()
    expect(device).not_.to_be_none()

    v1 = entity_registry.async_get_or_create(
        domain=DOMAIN,
        platform=Platform.SENSOR,
        unique_id=VOC_V1.unique_id,
        config_entry=entry,
        device_id=device.id,
    )

    v2 = entity_registry.async_get_or_create(
        domain=DOMAIN,
        platform=Platform.SENSOR,
        unique_id=VOC_V2.unique_id,
        config_entry=entry,
        device_id=device.id,
    )

    v3 = entity_registry.async_get_or_create(
        domain=DOMAIN,
        platform=Platform.SENSOR,
        unique_id=VOC_V3.unique_id,
        config_entry=entry,
        device_id=device.id,
    )

    await hass.async_block_till_done()
    expect(len(hass.states.async_all())).to_be(0)

    inject_bluetooth_service_info(
        hass,
        WAVE_SERVICE_INFO,
    )

    await hass.async_block_till_done()

    with patch_airthings_device_update():
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(len(hass.states.async_all()) > 0).to_be(True)

    # No migration should happen, unique id should be the same as before
    expect(entity_registry.async_get(v1.entity_id).unique_id).to_equal(VOC_V1.unique_id)
    expect(entity_registry.async_get(v2.entity_id).unique_id).to_equal(VOC_V2.unique_id)
    expect(entity_registry.async_get(v3.entity_id).unique_id).to_equal(VOC_V3.unique_id)


@test.skip("requires translation injection (translated sensor friendly_name)")
@test.cases(
    test.case("lux", unique_suffix="lux", expected_sensor_name="Illuminance"),
    test.case("noise", unique_suffix="noise", expected_sensor_name="Ambient noise"),
)
async def translation_keys_wave_enhance(
    unique_suffix: str,
    expected_sensor_name: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test that translated sensor names are correct."""
    entry = create_entry(hass, WAVE_ENHANCE_SERVICE_INFO, WAVE_ENHANCE_DEVICE_INFO)
    device = create_device(
        entry, device_registry, WAVE_ENHANCE_SERVICE_INFO, WAVE_ENHANCE_DEVICE_INFO
    )

    with (
        patch_async_ble_device_from_address(WAVE_ENHANCE_SERVICE_INFO.device),
        patch_async_discovered_service_info([WAVE_ENHANCE_SERVICE_INFO]),
        patch_airthings_ble(WAVE_ENHANCE_DEVICE_INFO),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(device).not_.to_be_none()
    expect(device.name).to_equal("Airthings Wave Enhance (123456)")

    unique_id = f"{WAVE_ENHANCE_DEVICE_INFO.address}_{unique_suffix}"
    entity_id = entity_registry.async_get_entity_id(Platform.SENSOR, DOMAIN, unique_id)
    expect(entity_id).not_.to_be_none()

    state = hass.states.get(entity_id)
    expect(state).not_.to_be_none()

    expected_value = WAVE_ENHANCE_DEVICE_INFO.sensors[unique_suffix]
    expect(state.state).to_equal(str(expected_value))

    expected_name = f"Airthings Wave Enhance (123456) {expected_sensor_name}"
    expect(state.attributes.get("friendly_name")).to_equal(expected_name)


@test
async def disabled_connectivity_mode_corentium_home_2(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test that translated sensor names are correct for disabled sensors."""
    entry = create_entry(
        hass,
        CORENTIUM_HOME_2_SERVICE_INFO,
        CORENTIUM_HOME_2_DEVICE_INFO,
    )
    device = create_device(
        entry,
        device_registry,
        CORENTIUM_HOME_2_SERVICE_INFO,
        CORENTIUM_HOME_2_DEVICE_INFO,
    )

    with (
        patch_async_ble_device_from_address(CORENTIUM_HOME_2_SERVICE_INFO.device),
        patch_async_discovered_service_info([CORENTIUM_HOME_2_SERVICE_INFO]),
        patch_airthings_ble(CORENTIUM_HOME_2_DEVICE_INFO),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    expect(device).not_.to_be_none()
    expect(device.name).to_equal("Airthings Corentium Home 2 (123456)")

    unique_id = f"{CORENTIUM_HOME_2_DEVICE_INFO.address}_connectivity_mode"

    entity_id = entity_registry.async_get_entity_id(Platform.SENSOR, DOMAIN, unique_id)
    expect(entity_id).not_.to_be_none()

    entity_entry = entity_registry.async_get(entity_id)
    expect(entity_entry).not_.to_be_none()
    expect(entity_entry.disabled).to_be(True)
    expect(entity_entry.disabled_by).to_be(er.RegistryEntryDisabler.INTEGRATION)


@test.skip("requires translation injection (entity_id slug connectivity_mode needs translation)")
@test.cases(
    test.case("none", source_value=None, expected_state=STATE_UNKNOWN),
    test.case("int", source_value=123, expected_state=STATE_UNKNOWN),
    test.case("float", source_value=45.6, expected_state=STATE_UNKNOWN),
    test.case("bluetooth", source_value="Bluetooth", expected_state="bluetooth"),
)
async def connectivity_mode(
    source_value: Any,
    expected_state: str,
    _trigger: int = Depends(_trigger_executor),
    _registry: None = Depends(entity_registry_enabled_by_default_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test that non-string connectivity mode values are handled correctly."""
    test_device = deepcopy(CORENTIUM_HOME_2_DEVICE_INFO)

    # Non-string value, will be mapped to 'unknown' state
    test_device.sensors["connectivity_mode"] = source_value

    entry = create_entry(hass, CORENTIUM_HOME_2_SERVICE_INFO, test_device)
    create_device(entry, device_registry, CORENTIUM_HOME_2_SERVICE_INFO, test_device)

    with (
        patch_async_ble_device_from_address(CORENTIUM_HOME_2_SERVICE_INFO.device),
        patch_async_discovered_service_info([CORENTIUM_HOME_2_SERVICE_INFO]),
        patch_airthings_ble(test_device),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get(
        "sensor.airthings_corentium_home_2_123456_connectivity_mode"
    )
    expect(state).not_.to_be_none()
    expect(state.state).to_equal(expected_state)


@test
async def scan_interval_migration_corentium_home_2(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test that radon device migration uses 30-minute scan interval."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=WAVE_SERVICE_INFO.address,
        data={},
    )
    entry.add_to_hass(hass)

    inject_bluetooth_service_info(hass, WAVE_SERVICE_INFO)

    with (
        patch_async_ble_device_from_address(WAVE_SERVICE_INFO.device),
        patch_airthings_ble(CORENTIUM_HOME_2_DEVICE_INFO) as mock_update,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Migration should have added device_model to entry data
        expect(DEVICE_MODEL in entry.data).to_be(True)
        expect(entry.data[DEVICE_MODEL]).to_equal(
            CORENTIUM_HOME_2_DEVICE_INFO.model.value
        )

        # Coordinator should have been configured with radon scan interval
        coordinator = entry.runtime_data
        expect(coordinator.update_interval).to_equal(
            timedelta(
                seconds=DEVICE_SPECIFIC_SCAN_INTERVAL.get(
                    CORENTIUM_HOME_2_DEVICE_INFO.model.value
                )
            )
        )

        # Should have 2 calls: 1 for migration + 1 for initial refresh
        expect(mock_update.call_count).to_be(2)

        # Fast forward by default interval (300s) - should NOT trigger update
        freezer.tick(DEFAULT_SCAN_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        expect(mock_update.call_count).to_be(2)

        # Fast forward to radon interval (1800s) - should trigger update
        freezer.tick(
            DEVICE_SPECIFIC_SCAN_INTERVAL.get(CORENTIUM_HOME_2_DEVICE_INFO.model.value)
        )
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        expect(mock_update.call_count).to_be(3)


@test.cases(
    test.case(
        "wave",
        service_info_key="wave",
    ),
    test.case(
        "wave_enhance",
        service_info_key="wave_enhance",
    ),
)
async def default_scan_interval_migration(
    service_info_key: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    freezer: FrozenDateTimeFactory = Depends(freezer_fixture),
) -> None:
    """Test that non-radon device migration uses default 5-minute scan interval."""
    pairs: dict[str, tuple[BluetoothServiceInfoBleak, AirthingsDevice]] = {
        "wave": (WAVE_SERVICE_INFO, WAVE_DEVICE_INFO),
        "wave_enhance": (WAVE_ENHANCE_SERVICE_INFO, WAVE_ENHANCE_DEVICE_INFO),
    }
    service_info, device_info = pairs[service_info_key]

    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id=service_info.address,
        data={},
    )
    entry.add_to_hass(hass)

    inject_bluetooth_service_info(hass, service_info)

    with (
        patch_async_ble_device_from_address(service_info.device),
        patch_airthings_ble(device_info) as mock_update,
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Migration should have added device_model to entry data
        expect(DEVICE_MODEL in entry.data).to_be(True)
        expect(entry.data[DEVICE_MODEL]).to_equal(device_info.model.value)

        # Coordinator should have been configured with default scan interval
        coordinator = entry.runtime_data
        expect(coordinator.update_interval).to_equal(
            timedelta(seconds=DEFAULT_SCAN_INTERVAL)
        )

        # Should have 2 calls: 1 for migration + 1 for initial refresh
        expect(mock_update.call_count).to_be(2)

        # Fast forward by default interval (300s) - SHOULD trigger update
        freezer.tick(DEFAULT_SCAN_INTERVAL)
        async_fire_time_changed(hass)
        await hass.async_block_till_done()
        expect(mock_update.call_count).to_be(3)
