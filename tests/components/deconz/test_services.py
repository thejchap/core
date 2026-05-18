"""deCONZ service tests (tryke port)."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.components.deconz.const import (
    CONF_BRIDGE_ID,
    CONF_MASTER_GATEWAY,
    DOMAIN,
)
from homeassistant.components.deconz.deconz_event import CONF_DECONZ_EVENT
from homeassistant.components.deconz.services import (
    SERVICE_CONFIGURE_DEVICE,
    SERVICE_DATA,
    SERVICE_DEVICE_REFRESH,
    SERVICE_ENTITY,
    SERVICE_FIELD,
    SERVICE_REMOVE_ORPHANED_ENTRIES,
)
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er

from tests.common import MockConfigEntry, async_capture_events
from tests.components.deconz._fixtures import (
    BRIDGE_ID,
    mock_put_request,
    register_get_request,
    setup_deconz,
)
from tests.hass_fixtures import (
    aioclient_mock,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture for tryke fixture-injection."""
    return 0


@test
async def configure_service_with_field(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request=Depends(mock_put_request),
) -> None:
    """Test that service invokes pydeconz with the correct path and data."""
    await setup_deconz(hass, aioclient)

    data = {
        SERVICE_FIELD: "/lights/2",
        CONF_BRIDGE_ID: BRIDGE_ID,
        SERVICE_DATA: {"on": True, "attr1": 10, "attr2": 20},
    }

    aioclient_with_put = put_request("/lights/2")

    await hass.services.async_call(
        DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data, blocking=True
    )
    expect(aioclient_with_put.mock_calls[1][2]).to_equal(
        {"on": True, "attr1": 10, "attr2": 20}
    )


@test
async def configure_service_with_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request=Depends(mock_put_request),
) -> None:
    """Test that service invokes pydeconz with the correct path and data."""
    await setup_deconz(
        hass,
        aioclient,
        light_payload={
            "name": "Test",
            "state": {"reachable": True},
            "type": "Dimmable light",
            "uniqueid": "00:00:00:00:00:00:00:01-00",
        },
    )

    data = {
        SERVICE_ENTITY: "light.test",
        SERVICE_DATA: {"on": True, "attr1": 10, "attr2": 20},
    }
    aioclient_with_put = put_request("/lights/0")

    await hass.services.async_call(
        DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data, blocking=True
    )
    expect(aioclient_with_put.mock_calls[1][2]).to_equal(
        {"on": True, "attr1": 10, "attr2": 20}
    )


@test
async def configure_service_with_entity_and_field(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request=Depends(mock_put_request),
) -> None:
    """Test that service invokes pydeconz with the correct path and data."""
    await setup_deconz(
        hass,
        aioclient,
        light_payload={
            "name": "Test",
            "state": {"reachable": True},
            "type": "Dimmable light",
            "uniqueid": "00:00:00:00:00:00:00:01-00",
        },
    )

    data = {
        SERVICE_ENTITY: "light.test",
        SERVICE_FIELD: "/state",
        SERVICE_DATA: {"on": True, "attr1": 10, "attr2": 20},
    }
    aioclient_with_put = put_request("/lights/0/state")

    await hass.services.async_call(
        DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data, blocking=True
    )
    expect(aioclient_with_put.mock_calls[1][2]).to_equal(
        {"on": True, "attr1": 10, "attr2": 20}
    )


@test
async def configure_service_with_faulty_bridgeid(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that service fails on a bad bridge id."""
    await setup_deconz(hass, aioclient)
    aioclient.clear_requests()

    data = {
        CONF_BRIDGE_ID: "Bad bridge id",
        SERVICE_FIELD: "/lights/1",
        SERVICE_DATA: {"on": True},
    }

    await hass.services.async_call(DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data)
    await hass.async_block_till_done()

    expect(len(aioclient.mock_calls)).to_equal(0)


@test
async def configure_service_with_faulty_field(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that service fails on a bad field."""
    await setup_deconz(hass, aioclient)

    data = {SERVICE_FIELD: "light/2", SERVICE_DATA: {}}

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data
        )


@test
async def configure_service_with_faulty_entity(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that service on a non existing entity."""
    await setup_deconz(hass, aioclient)
    aioclient.clear_requests()

    data = {
        SERVICE_ENTITY: "light.nonexisting",
        SERVICE_DATA: {},
    }

    await hass.services.async_call(DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data)
    await hass.async_block_till_done()

    expect(len(aioclient.mock_calls)).to_equal(0)


@test
async def calling_service_with_no_master_gateway_fails(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that service call fails when no master gateway exist."""
    await setup_deconz(hass, aioclient, options={CONF_MASTER_GATEWAY: False})
    aioclient.clear_requests()

    data = {
        SERVICE_FIELD: "/lights/1",
        SERVICE_DATA: {"on": True},
    }

    await hass.services.async_call(DOMAIN, SERVICE_CONFIGURE_DEVICE, service_data=data)
    await hass.async_block_till_done()

    expect(len(aioclient.mock_calls)).to_equal(0)


@test
async def service_refresh_devices(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that service can refresh devices."""
    await setup_deconz(hass, aioclient)
    expect(len(hass.states.async_all())).to_equal(0)

    aioclient.clear_requests()

    refresh_payload: dict[str, Any] = {
        "groups": {
            "1": {
                "id": "Group 1 id",
                "name": "Group 1 name",
                "type": "LightGroup",
                "state": {},
                "action": {},
                "scenes": [{"id": "1", "name": "Scene 1"}],
                "lights": ["1"],
            }
        },
        "lights": {
            "1": {
                "name": "Light 1 name",
                "state": {"reachable": True},
                "type": "Dimmable light",
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            }
        },
        "sensors": {
            "1": {
                "name": "Sensor 1 name",
                "type": "ZHALightLevel",
                "state": {"lightlevel": 30000, "dark": False},
                "config": {"reachable": True},
                "uniqueid": "00:00:00:00:00:00:00:02-00",
            }
        },
    }
    register_get_request(aioclient, deconz_payload=refresh_payload)

    await hass.services.async_call(
        DOMAIN, SERVICE_DEVICE_REFRESH, service_data={CONF_BRIDGE_ID: BRIDGE_ID}
    )
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(5)


@test
async def service_refresh_devices_trigger_no_state_update(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Verify that gateway.ignore_state_updates are honored."""
    await setup_deconz(
        hass,
        aioclient,
        sensor_payload={
            "name": "Switch 1",
            "type": "ZHASwitch",
            "state": {"buttonevent": 1000},
            "config": {"battery": 100},
            "uniqueid": "00:00:00:00:00:00:00:01-00",
        },
    )
    expect(len(hass.states.async_all())).to_equal(1)

    captured_events = async_capture_events(hass, CONF_DECONZ_EVENT)

    aioclient.clear_requests()

    refresh_payload: dict[str, Any] = {
        "groups": {
            "1": {
                "id": "Group 1 id",
                "name": "Group 1 name",
                "type": "LightGroup",
                "state": {},
                "action": {},
                "scenes": [{"id": "1", "name": "Scene 1"}],
                "lights": ["1"],
            }
        },
        "lights": {
            "1": {
                "name": "Light 1 name",
                "state": {"reachable": True},
                "type": "Dimmable light",
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            }
        },
        "sensors": {
            "0": {
                "name": "Switch 1",
                "type": "ZHASwitch",
                "state": {"buttonevent": 1000},
                "config": {"battery": 100},
                "uniqueid": "00:00:00:00:00:00:00:01-00",
            }
        },
    }
    register_get_request(aioclient, deconz_payload=refresh_payload)

    await hass.services.async_call(
        DOMAIN, SERVICE_DEVICE_REFRESH, service_data={CONF_BRIDGE_ID: BRIDGE_ID}
    )
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(5)
    expect(len(captured_events)).to_equal(0)


@test
async def remove_orphaned_entries_service(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test service works and also don't remove more than expected."""
    config_entry_setup: MockConfigEntry = await setup_deconz(
        hass,
        aioclient,
        light_payload={
            "name": "Light 0 name",
            "state": {"reachable": True},
            "type": "Dimmable light",
            "uniqueid": "00:00:00:00:00:00:00:01-00",
        },
        sensor_payload={
            "name": "Switch 1",
            "type": "ZHASwitch",
            "state": {"buttonevent": 1000, "gesture": 1},
            "config": {"battery": 100},
            "uniqueid": "00:00:00:00:00:00:00:03-00",
        },
    )

    device = device_registry.async_get_or_create(
        config_entry_id=config_entry_setup.entry_id,
        identifiers={(DOMAIN, BRIDGE_ID)},
    )

    device_registry.async_get_or_create(
        config_entry_id=config_entry_setup.entry_id,
        identifiers={(DOMAIN, "orphaned")},
    )

    expect(
        len(
            [
                entry
                for entry in device_registry.devices.values()
                if config_entry_setup.entry_id in entry.config_entries
            ]
        )
    ).to_equal(4)  # Gateway, light, switch and orphan

    entity_registry.async_get_or_create(
        SENSOR_DOMAIN,
        DOMAIN,
        "12345",
        suggested_object_id="Orphaned sensor",
        config_entry=config_entry_setup,
        device_id=device.id,
    )

    expect(
        len(
            er.async_entries_for_config_entry(
                entity_registry, config_entry_setup.entry_id
            )
        )
    ).to_equal(3)  # Light, switch battery and orphan

    await hass.services.async_call(
        DOMAIN,
        SERVICE_REMOVE_ORPHANED_ENTRIES,
        service_data={CONF_BRIDGE_ID: BRIDGE_ID},
    )
    await hass.async_block_till_done()

    expect(
        len(
            [
                entry
                for entry in device_registry.devices.values()
                if config_entry_setup.entry_id in entry.config_entries
            ]
        )
    ).to_equal(3)  # Gateway, light and switch

    expect(
        len(
            er.async_entries_for_config_entry(
                entity_registry, config_entry_setup.entry_id
            )
        )
    ).to_equal(2)  # Light and switch battery
