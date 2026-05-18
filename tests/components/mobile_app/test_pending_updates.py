"""Tests for mobile_app pending updates functionality."""

from http import HTTPStatus
from typing import Any

from aiohttp.test_utils import TestClient
from tryke import Depends, expect, fixture, test

from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ._fixtures import (
    create_registrations as create_registrations_fixture,
    webhook_client as webhook_client_fixture,
)

from tests.hass_fixtures import (
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


@test
async def pending_update_applied_when_entity_enabled(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that updates sent while disabled are applied when entity is re-enabled."""
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
                "unit_of_measurement": PERCENTAGE,
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("100")

    entity_registry.async_update_entity(
        "sensor.test_1_battery_state", disabled_by=er.RegistryEntryDisabler.USER
    )
    await hass.async_block_till_done()

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": 50,
                "type": "sensor",
                "unique_id": "battery_state",
                "unit_of_measurement": PERCENTAGE,
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)
    await hass.async_block_till_done()

    entity_registry.async_update_entity("sensor.test_1_battery_state", disabled_by=None)

    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("50")


@test
async def pending_update_with_attributes(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that pending updates preserve all attributes."""
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
                "attributes": {"charging": True, "voltage": 4.2},
                "icon": "mdi:battery-charging",
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)
    await hass.async_block_till_done()

    entity_registry.async_update_entity(
        "sensor.test_1_battery_state", disabled_by=er.RegistryEntryDisabler.USER
    )
    await hass.async_block_till_done()

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": 50,
                "type": "sensor",
                "unique_id": "battery_state",
                "attributes": {"charging": False, "voltage": 3.7},
                "icon": "mdi:battery-50",
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)
    await hass.async_block_till_done()

    entity_registry.async_update_entity("sensor.test_1_battery_state", disabled_by=None)

    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("50")
    expect(entity.attributes["charging"]).to_be(False)
    expect(entity.attributes["voltage"]).to_equal(3.7)
    expect(entity.attributes["icon"]).to_equal("mdi:battery-50")


@test
async def pending_update_overwritten_by_newer_update(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that newer pending updates overwrite older ones."""
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
    await hass.async_block_till_done()

    entity_registry.async_update_entity(
        "sensor.test_1_battery_state", disabled_by=er.RegistryEntryDisabler.USER
    )
    await hass.async_block_till_done()

    await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": 75,
                "type": "sensor",
                "unique_id": "battery_state",
            },
        },
    )
    await hass.async_block_till_done()

    await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": 25,
                "type": "sensor",
                "unique_id": "battery_state",
            },
        },
    )
    await hass.async_block_till_done()

    entity_registry.async_update_entity("sensor.test_1_battery_state", disabled_by=None)

    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("25")


@test
async def pending_update_not_stored_on_enabled_entities(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that enabled entities receive updates immediately."""
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
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("100")

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": 50,
                "type": "sensor",
                "unique_id": "battery_state",
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("50")


@test
async def pending_update_fallback_to_restore_state(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that restored state is used when no pending update exists."""
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
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("100")

    await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "state": 75,
                    "type": "sensor",
                    "unique_id": "battery_state",
                }
            ],
        },
    )
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("75")

    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("75")


@test
async def multiple_pending_updates_for_different_sensors(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that multiple sensors can be updated while disabled and applied when re-enabled."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    for unique_id, state in (("battery_state", 100), ("battery_temp", 25)):
        reg_resp = await webhook_client.post(
            webhook_url,
            json={
                "type": "register_sensor",
                "data": {
                    "name": unique_id.replace("_", " ").title(),
                    "state": state,
                    "type": "sensor",
                    "unique_id": unique_id,
                },
            },
        )
        expect(reg_resp.status).to_equal(HTTPStatus.CREATED)

    await hass.async_block_till_done()

    entity_registry.async_update_entity(
        "sensor.test_1_battery_state", disabled_by=er.RegistryEntryDisabler.USER
    )
    entity_registry.async_update_entity(
        "sensor.test_1_battery_temp", disabled_by=er.RegistryEntryDisabler.USER
    )
    await hass.async_block_till_done()

    await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery State",
                "state": 50,
                "type": "sensor",
                "unique_id": "battery_state",
            },
        },
    )

    await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Battery Temp",
                "state": 30,
                "type": "sensor",
                "unique_id": "battery_temp",
            },
        },
    )
    await hass.async_block_till_done()

    entity_registry.async_update_entity("sensor.test_1_battery_state", disabled_by=None)
    entity_registry.async_update_entity("sensor.test_1_battery_temp", disabled_by=None)

    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    battery_state = hass.states.get("sensor.test_1_battery_state")
    battery_temp = hass.states.get("sensor.test_1_battery_temp")

    expect(battery_state is not None).to_be(True)
    expect(battery_state.state).to_equal("50")
    expect(battery_temp is not None).to_be(True)
    expect(battery_temp.state).to_equal("30")


@test
async def update_sensor_states_with_pending_updates(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that update_sensor_states updates are applied when entity is re-enabled."""
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
                "unit_of_measurement": PERCENTAGE,
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("100")

    entity_registry.async_update_entity(
        "sensor.test_1_battery_state", disabled_by=er.RegistryEntryDisabler.USER
    )
    await hass.async_block_till_done()

    resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "state": 75,
                    "type": "sensor",
                    "unique_id": "battery_state",
                }
            ],
        },
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    await hass.async_block_till_done()

    entity_registry.async_update_entity("sensor.test_1_battery_state", disabled_by=None)

    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("75")


@test
async def update_sensor_states_always_stores_pending(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that update_sensor_states applies updates to enabled entities."""
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
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("100")

    resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "update_sensor_states",
            "data": [
                {
                    "state": 50,
                    "type": "sensor",
                    "unique_id": "battery_state",
                }
            ],
        },
    )

    expect(resp.status).to_equal(HTTPStatus.OK)
    await hass.async_block_till_done()

    entity = hass.states.get("sensor.test_1_battery_state")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("50")


@test
async def binary_sensor_pending_update(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    create_registrations: tuple[dict[str, Any], dict[str, Any]] = Depends(
        create_registrations_fixture
    ),
    webhook_client: TestClient = Depends(webhook_client_fixture),
) -> None:
    """Test that binary sensor updates are applied when entity is re-enabled."""
    webhook_id = create_registrations[1]["webhook_id"]
    webhook_url = f"/api/webhook/{webhook_id}"

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Motion Detected",
                "state": False,
                "type": "binary_sensor",
                "unique_id": "motion_sensor",
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)
    await hass.async_block_till_done()

    entity = hass.states.get("binary_sensor.test_1_motion_detected")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("off")

    entity_registry.async_update_entity(
        "binary_sensor.test_1_motion_detected",
        disabled_by=er.RegistryEntryDisabler.USER,
    )
    await hass.async_block_till_done()

    reg_resp = await webhook_client.post(
        webhook_url,
        json={
            "type": "register_sensor",
            "data": {
                "name": "Motion Detected",
                "state": True,
                "type": "binary_sensor",
                "unique_id": "motion_sensor",
            },
        },
    )

    expect(reg_resp.status).to_equal(HTTPStatus.CREATED)
    await hass.async_block_till_done()

    entity_registry.async_update_entity(
        "binary_sensor.test_1_motion_detected", disabled_by=None
    )

    config_entry = hass.config_entries.async_entries("mobile_app")[1]
    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    entity = hass.states.get("binary_sensor.test_1_motion_detected")
    expect(entity is not None).to_be(True)
    expect(entity.state).to_equal("on")
