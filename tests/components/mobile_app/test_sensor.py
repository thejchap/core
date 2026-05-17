"""Entity tests for mobile_app."""

from http import HTTPStatus
from typing import Any
from unittest.mock import patch

from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from homeassistant.components.mobile_app.const import (
    ATTR_SENSOR_ATTRIBUTES,
    ATTR_SENSOR_ICON,
    ATTR_SENSOR_NAME,
    ATTR_SENSOR_STATE,
    ATTR_SENSOR_TYPE,
    ATTR_SENSOR_UNIQUE_ID,
)
from homeassistant.components.sensor import SensorDeviceClass
from homeassistant.const import (
    CONF_WEBHOOK_ID,
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util.unit_system import (
    METRIC_SYSTEM,
    US_CUSTOMARY_SYSTEM,
    UnitSystem,
)

from ._fixtures import (
    create_registrations as create_registrations_fixture,
    webhook_client as webhook_client_fixture,
)

from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> int:
    """Anchor for tryke fixture resolution."""
    return 0


@test.cases(
    test.case(
        "metric",
        unit_system=METRIC_SYSTEM,
        state_unit=UnitOfTemperature.CELSIUS,
        state1=100,
        state2=123,
    ),
    test.case(
        "us_customary",
        unit_system=US_CUSTOMARY_SYSTEM,
        state_unit=UnitOfTemperature.FAHRENHEIT,
        state1=212,
        state2=253.4,
    ),
)
async def sensor(
    unit_system: UnitSystem,
    state_unit: UnitOfTemperature,
    state1: float,
    state2: float,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that sensors can be registered and updated."""
    hass.config.units = unit_system

    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "attributes": {"foo": "bar"},
                "device_class": "temperature",
                "icon": "mdi:battery",
                "name": "Battery Temperature",
                "state": 100,
                "type": "sensor",
                "entity_category": "diagnostic",
                "unique_id": "battery_temp",
                "state_class": "measurement",
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)

    json = await reg_resp.json()
    expect(json).to_equal({"success": True})
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_temperature")
    expect(entity is not None).to_be(True)

    expect(entity.attributes["device_class"]).to_equal("temperature")
    expect(entity.attributes["icon"]).to_equal("mdi:battery")
    # unit of temperature sensor is automatically converted to the system UoM
    expect(entity.attributes["unit_of_measurement"]).to_equal(state_unit)
    expect(entity.attributes["foo"]).to_equal("bar")
    expect(entity.attributes["state_class"]).to_equal("measurement")
    expect(entity.domain).to_equal("sensor")
    expect(entity.name).to_equal("Test 1 Battery Temperature")
    expect(float(entity.state)).to_equal(state1)

    expect(
        entity_registry.async_get(
            "sensor.test_1_battery_temperature"
        ).entity_category
    ).to_equal("diagnostic")

    update_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "icon": "mdi:battery-unknown",
                    "state": 123,
                    "type": "sensor",
                    "unique_id": "battery_temp",
                },
                # This invalid data should not invalidate whole request
                {"type": "sensor", "unique_id": "invalid_state", "invalid": "data"},
            ],
        },
    )

    expect(update_resp.status).to_equal(HTTPStatus.OK)

    json = await update_resp.json()
    expect(json["invalid_state"]["success"]).to_be(False)

    updated_entity = hass.states.get("sensor.test_1_battery_temperature")
    expect(float(updated_entity.state)).to_equal(state2)
    expect("foo" not in updated_entity.attributes).to_be(True)

    expect(len(device_registry.devices)).to_equal(len(create_registrations))

    # Reload to verify state is restored
    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    unloaded_entity = hass.states.get("sensor.test_1_battery_temperature")
    expect(unloaded_entity.state).to_equal(STATE_UNAVAILABLE)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()
    restored_entity = hass.states.get("sensor.test_1_battery_temperature")
    expect(restored_entity.state).to_equal(updated_entity.state)
    expect(restored_entity.attributes).to_equal(updated_entity.attributes)


@test.cases(
    test.case(
        "metric_match",
        unique_id="battery_temperature",
        unit_system=METRIC_SYSTEM,
        state_unit=UnitOfTemperature.CELSIUS,
        state1=100,
        state2=123,
    ),
    test.case(
        "us_match",
        unique_id="battery_temperature",
        unit_system=US_CUSTOMARY_SYSTEM,
        state_unit=UnitOfTemperature.FAHRENHEIT,
        state1=212,
        state2=253,
    ),
    test.case(
        "us_no_match",
        unique_id="battery_temp",
        unit_system=US_CUSTOMARY_SYSTEM,
        state_unit=UnitOfTemperature.FAHRENHEIT,
        state1=212,
        state2=123,
    ),
)
async def sensor_migration(
    unique_id: str,
    unit_system: UnitSystem,
    state_unit: UnitOfTemperature,
    state1: float,
    state2: float,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test migration to RestoreSensor."""
    hass.config.units = unit_system

    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "attributes": {"foo": "bar"},
                "device_class": "temperature",
                "icon": "mdi:battery",
                "name": "Battery Temperature",
                "state": 100,
                "type": "sensor",
                "entity_category": "diagnostic",
                "unique_id": unique_id,
                "state_class": "measurement",
                "unit_of_measurement": UnitOfTemperature.CELSIUS,
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)

    json = await reg_resp.json()
    expect(json).to_equal({"success": True})
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_temperature")
    expect(entity is not None).to_be(True)

    expect(entity.attributes["device_class"]).to_equal("temperature")
    expect(entity.attributes["icon"]).to_equal("mdi:battery")
    # unit of temperature sensor is automatically converted to the system UoM
    expect(entity.attributes["unit_of_measurement"]).to_equal(state_unit)
    expect(entity.attributes["foo"]).to_equal("bar")
    expect(entity.attributes["state_class"]).to_equal("measurement")
    expect(entity.domain).to_equal("sensor")
    expect(entity.name).to_equal("Test 1 Battery Temperature")
    expect(float(entity.state)).to_equal(state1)

    # Reload to verify state is restored
    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_unload(config_entry.entry_id)
    await hass.async_block_till_done()
    unloaded_entity = hass.states.get("sensor.test_1_battery_temperature")
    expect(unloaded_entity.state).to_equal(STATE_UNAVAILABLE)

    # Simulate migration to RestoreSensor
    with patch(
        "homeassistant.helpers.restore_state.RestoreEntity.async_get_last_extra_data",
        return_value=None,
    ):
        await hass.config_entries.async_setup(config_entry.entry_id)
        await hass.async_block_till_done()
    restored_entity = hass.states.get("sensor.test_1_battery_temperature")
    expect(restored_entity.state).to_equal("unknown")
    expect(restored_entity.attributes).to_equal(entity.attributes)

    # Test unit conversion is working
    update_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "icon": "mdi:battery-unknown",
                    "state": 123,
                    "type": "sensor",
                    "unique_id": unique_id,
                },
            ],
        },
    )

    expect(update_resp.status).to_equal(HTTPStatus.OK)

    updated_entity = hass.states.get("sensor.test_1_battery_temperature")
    expect(round(float(updated_entity.state), 0)).to_equal(state2)
    expect("foo" not in updated_entity.attributes).to_be(True)


@test
async def sensor_must_register(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that sensors must be registered before updating."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"
    resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [{"state": 123, "type": "sensor", "unique_id": "battery_state"}],
        },
    )

    expect(resp.status).to_equal(HTTPStatus.OK)

    json = await resp.json()
    expect(json["battery_state"]["success"]).to_be(False)
    expect(json["battery_state"]["error"]["code"]).to_equal("not_registered")


@test
async def sensor_id_no_dupes(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that a duplicate unique ID in registration updates the sensor."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    payload = {
        "type": "register_sensor",
        "data": {
            "attributes": {"foo": "bar"},
            "device_class": "battery",
            "icon": "mdi:battery",
            "name": "Battery State",
            "state": 100,
            "type": "sensor",
            "unique_id": "battery_state",
            "unit_of_measurement": PERCENTAGE,
        },
    }

    reg_resp = await webhook_client.post(webhook_url, json=payload)

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)

    reg_json = await reg_resp.json()
    expect(reg_json).to_equal({"success": True})
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)

    expect(entity.attributes["device_class"]).to_equal("battery")
    expect(entity.attributes["icon"]).to_equal("mdi:battery")
    expect(entity.attributes["unit_of_measurement"]).to_equal(PERCENTAGE)
    expect(entity.attributes["foo"]).to_equal("bar")
    expect(entity.domain).to_equal("sensor")
    expect(entity.name).to_equal("Test 1 Battery State")
    expect(entity.state).to_equal("100")

    payload["data"]["state"] = 99
    dupe_resp = await webhook_client.post(webhook_url, json=payload)

    expect(dupe_resp.status).to_equal(HTTPStatus.CREATED)
    dupe_reg_json = await dupe_resp.json()
    expect(dupe_reg_json).to_equal({"success": True})
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)

    expect(entity.attributes["device_class"]).to_equal("battery")
    expect(entity.attributes["icon"]).to_equal("mdi:battery")
    expect(entity.attributes["unit_of_measurement"]).to_equal(PERCENTAGE)
    expect(entity.attributes["foo"]).to_equal("bar")
    expect(entity.domain).to_equal("sensor")
    expect(entity.name).to_equal("Test 1 Battery State")
    expect(entity.state).to_equal("99")


@test
async def register_sensor_no_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that sensors can be registered, when there is no (unknown) state."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": None,
                "type": "sensor",
                "unique_id": "battery_state",
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)

    json = await reg_resp.json()
    expect(json).to_equal({"success": True})
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)

    expect(entity.domain).to_equal("sensor")
    expect(entity.name).to_equal("Test 1 Battery State")
    expect(entity.state).to_equal(STATE_UNKNOWN)

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Backup Battery State",
                "type": "sensor",
                "unique_id": "backup_battery_state",
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)

    json = await reg_resp.json()
    expect(json).to_equal({"success": True})
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_backup_battery_state")
    expect(entity is not None).to_be(True)

    expect(entity.domain).to_equal("sensor")
    expect(entity.name).to_equal("Test 1 Backup Battery State")
    expect(entity.state).to_equal(STATE_UNKNOWN)


@test
async def update_sensor_no_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that sensors can be updated, when there is no (unknown) state."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": 100,
                "type": "sensor",
                "unique_id": "battery_state",
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)

    json = await reg_resp.json()
    expect(json).to_equal({"success": True})
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("100")

    update_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [{"state": None, "type": "sensor", "unique_id": "battery_state"}],
        },
    )

    expect(update_resp.status).to_equal(HTTPStatus.OK)

    json = await update_resp.json()
    expect(json).to_equal({"battery_state": {"success": True}})

    updated_entity = hass.states.get("sensor.test_1_battery_state")
    expect(updated_entity.state).to_equal(STATE_UNKNOWN)


@test.cases(
    test.case(
        "date",
        device_class=SensorDeviceClass.DATE,
        native_value="2021-11-18",
        state_value="2021-11-18",
    ),
    test.case(
        "timestamp_utc",
        device_class=SensorDeviceClass.TIMESTAMP,
        native_value="2021-11-18T20:25:00+00:00",
        state_value="2021-11-18T20:25:00+00:00",
    ),
    test.case(
        "timestamp_offset",
        device_class=SensorDeviceClass.TIMESTAMP,
        native_value="2021-11-18 20:25:00+01:00",
        state_value="2021-11-18T19:25:00+00:00",
    ),
    test.case(
        "timestamp_unavailable",
        device_class=SensorDeviceClass.TIMESTAMP,
        native_value="unavailable",
        state_value=STATE_UNAVAILABLE,
    ),
    test.case(
        "timestamp_unknown",
        device_class=SensorDeviceClass.TIMESTAMP,
        native_value="unknown",
        state_value=STATE_UNKNOWN,
    ),
)
async def sensor_datetime(
    device_class: SensorDeviceClass,
    native_value: str,
    state_value: str,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that sensors can be registered and updated."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "device_class": device_class,
                "name": "Datetime sensor test",
                "state": native_value,
                "type": "sensor",
                "unique_id": "super_unique",
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)

    json = await reg_resp.json()
    expect(json).to_equal({"success": True})
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_datetime_sensor_test")
    expect(entity is not None).to_be(True)

    expect(entity.attributes["device_class"]).to_equal(device_class)
    expect(entity.domain).to_equal("sensor")
    expect(entity.state).to_equal(state_value)


@test
async def default_disabling_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that sensors can be disabled by default upon registration."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "type": "sensor",
                "unique_id": "battery_state",
                "disabled": True,
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)

    json = await reg_resp.json()
    expect(json).to_equal({"success": True})
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity).to_be(None)

    expect(
        entity_registry.async_get("sensor.test_1_battery_state").disabled_by
    ).to_equal(er.RegistryEntryDisabler.INTEGRATION)


@test
async def updating_disabled_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that sensors return error if disabled in instance."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": None,
                "type": "sensor",
                "unique_id": "battery_state",
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)

    update_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "icon": "mdi:battery-unknown",
                    "state": 123,
                    "type": "sensor",
                    "unique_id": "battery_state",
                },
            ],
        },
    )

    expect(update_resp.status).to_equal(HTTPStatus.OK)

    json = await update_resp.json()
    expect(json["battery_state"]["success"]).to_be(True)
    expect("is_disabled" not in json["battery_state"]).to_be(True)

    entity_registry.async_update_entity(
        "sensor.test_1_battery_state", disabled_by=er.RegistryEntryDisabler.USER
    )

    update_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "icon": "mdi:battery-unknown",
                    "state": 123,
                    "type": "sensor",
                    "unique_id": "battery_state",
                },
            ],
        },
    )

    expect(update_resp.status).to_equal(HTTPStatus.OK)

    json = await update_resp.json()
    expect(json["battery_state"]["success"]).to_be(True)
    expect(json["battery_state"]["is_disabled"]).to_be(True)


@test
async def recreate_correct_from_entity_registry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that sensors can be re-created from entity registry."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "device_class": "battery",
                "icon": "mdi:battery",
                "name": "Battery State",
                "state": 100,
                "type": "sensor",
                "unique_id": "battery_state",
                "unit_of_measurement": PERCENTAGE,
                "state_class": "measurement",
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)

    update_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "icon": "mdi:battery-unknown",
                    "state": 123,
                    "type": "sensor",
                    "unique_id": "battery_state",
                },
            ],
        },
    )

    expect(update_resp.status).to_equal(HTTPStatus.OK)

    entity = hass.states.get("sensor.test_1_battery_state")

    expect(entity is not None).to_be(True)
    entity_entry = entity_registry.async_get("sensor.test_1_battery_state")
    expect(entity_entry is not None).to_be(True)

    expect(entity_entry.capabilities).to_equal({"state_class": "measurement"})

    entry = hass.config_entries.async_entries("mobile_app")[1]

    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(hass.states.get("sensor.test_1_battery_state").state).to_equal(
        STATE_UNAVAILABLE
    )

    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    entity_entry = entity_registry.async_get("sensor.test_1_battery_state")
    expect(entity_entry is not None).to_be(True)
    expect(hass.states.get("sensor.test_1_battery_state") is not None).to_be(True)

    expect(entity_entry.capabilities).to_equal({"state_class": "measurement"})


@test
async def dispatcher_cleanup_on_unload(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that dispatcher connections are cleaned up on config entry unload."""

    webhook_id = create_registrations[1]["webhook_id"]
    entry = hass.config_entries.async_entries("mobile_app")[1]

    # Send a dispatcher signal when config entry is loaded
    async_dispatcher_send(
        hass,
        "mobile_app_sensor_register",
        {
            CONF_WEBHOOK_ID: webhook_id,
            ATTR_SENSOR_NAME: "Test Before Unload",
            ATTR_SENSOR_STATE: 42,
            ATTR_SENSOR_TYPE: "sensor",
            ATTR_SENSOR_UNIQUE_ID: "test_before_unload",
            ATTR_SENSOR_ICON: "mdi:test",
            ATTR_SENSOR_ATTRIBUTES: {},
        },
    )
    await hass.async_block_till_done()

    expect(hass.states.get("sensor.test_1_test_before_unload") is not None).to_be(True)

    # Unload the config entry
    expect(await hass.config_entries.async_unload(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    # Send another dispatcher signal after unload
    async_dispatcher_send(
        hass,
        "mobile_app_sensor_register",
        {
            CONF_WEBHOOK_ID: webhook_id,
            ATTR_SENSOR_NAME: "Test After Unload",
            ATTR_SENSOR_STATE: 99,
            ATTR_SENSOR_TYPE: "sensor",
            ATTR_SENSOR_UNIQUE_ID: "test_after_unload",
            ATTR_SENSOR_ICON: "mdi:test",
            ATTR_SENSOR_ATTRIBUTES: {},
        },
    )
    await hass.async_block_till_done()

    # The sensor should not be created because dispatcher was cleaned up
    expect(hass.states.get("sensor.test_1_test_after_unload")).to_be(None)

    # Reload the config entry
    expect(await hass.config_entries.async_setup(entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    # Send dispatcher signal after reload
    async_dispatcher_send(
        hass,
        "mobile_app_sensor_register",
        {
            CONF_WEBHOOK_ID: webhook_id,
            ATTR_SENSOR_NAME: "Test After Reload",
            ATTR_SENSOR_STATE: 123,
            ATTR_SENSOR_TYPE: "sensor",
            ATTR_SENSOR_UNIQUE_ID: "test_after_reload",
            ATTR_SENSOR_ICON: "mdi:test",
            ATTR_SENSOR_ATTRIBUTES: {},
        },
    )
    await hass.async_block_till_done()

    # This sensor should be created successfully after reload
    expect(hass.states.get("sensor.test_1_test_after_reload") is not None).to_be(True)
    expect(hass.states.get("sensor.test_1_test_after_reload").state).to_equal("123")
