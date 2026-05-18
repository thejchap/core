"""deCONZ binary sensor platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.deconz.const import (
    CONF_ALLOW_CLIP_SENSOR,
    CONF_ALLOW_NEW_DEVICES,
    CONF_MASTER_GATEWAY,
    DOMAIN,
)
from homeassistant.components.deconz.services import SERVICE_DEVICE_REFRESH
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.components.deconz._fixtures import (
    mock_websocket as mock_websocket_fixture,
    register_get_request,
    setup_deconz,
)
from tests.hass_fixtures import (
    aioclient_mock,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture for tryke fixture-injection."""
    return 0


@fixture
def sensor_ws_data(
    mock_websocket: Any = Depends(mock_websocket_fixture),
) -> Callable[[dict[str, Any]], Any]:
    """Return a callable that sends sensor websocket events."""

    async def send(data: dict[str, Any]) -> None:
        payload: dict[str, Any] = {"r": "sensors"}
        payload.update(data)
        payload.setdefault("t", "event")
        payload.setdefault("e", "changed")
        payload.setdefault("id", "0")
        await mock_websocket(data=payload)

    return send


@test.skip("snapshot test - parametrize id mismatch with pytest snapshots")
async def binary_sensors() -> None:
    """Snapshot-based parametrize test cannot reuse pytest .ambr ids."""


@test
async def not_allow_clip_sensor(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that CLIP sensors are not allowed."""
    sensor_payload = {
        "name": "CLIP presence sensor",
        "type": "CLIPPresence",
        "state": {"presence": False},
        "config": {},
        "uniqueid": "00:00:00:00:00:00:00:02-00",
    }
    await setup_deconz(
        hass,
        aioclient,
        options={CONF_ALLOW_CLIP_SENSOR: False},
        sensor_payload=sensor_payload,
    )
    expect(len(hass.states.async_all())).to_be(0)


@test
async def allow_clip_sensor(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that CLIP sensors can be allowed."""
    sensor_payload = {
        "1": {
            "name": "Presence sensor",
            "type": "ZHAPresence",
            "state": {"presence": False},
            "config": {"on": True, "reachable": True},
            "uniqueid": "00:00:00:00:00:00:00:00-00",
        },
        "2": {
            "name": "CLIP presence sensor",
            "type": "CLIPPresence",
            "state": {"presence": False},
            "config": {},
            "uniqueid": "00:00:00:00:00:00:00:02-00",
        },
        "3": {
            "config": {"on": True, "reachable": True},
            "etag": "fda064fca03f17389d0799d7cb1883ee",
            "manufacturername": "Philips",
            "modelid": "CLIPGenericFlag",
            "name": "Clip Flag Boot Time",
            "state": {"flag": True, "lastupdated": "2021-09-30T07:09:06.281"},
            "swversion": "1.0",
            "type": "CLIPGenericFlag",
            "uniqueid": "/sensors/3",
        },
    }
    config_entry_setup = await setup_deconz(
        hass,
        aioclient,
        options={CONF_ALLOW_CLIP_SENSOR: True},
        sensor_payload=sensor_payload,
    )

    expect(len(hass.states.async_all())).to_be(3)
    expect(hass.states.get("binary_sensor.presence_sensor").state).to_be(STATE_OFF)
    expect(hass.states.get("binary_sensor.clip_presence_sensor").state).to_be(STATE_OFF)
    expect(hass.states.get("binary_sensor.clip_flag_boot_time").state).to_be(STATE_ON)

    # Disallow clip sensors
    hass.config_entries.async_update_entry(
        config_entry_setup, options={CONF_ALLOW_CLIP_SENSOR: False}
    )
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_be(1)
    expect(hass.states.get("binary_sensor.clip_presence_sensor")).to_be(None)
    expect(hass.states.get("binary_sensor.clip_flag_boot_time")).to_be(None)

    # Allow clip sensors
    hass.config_entries.async_update_entry(
        config_entry_setup, options={CONF_ALLOW_CLIP_SENSOR: True}
    )
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_be(3)
    expect(hass.states.get("binary_sensor.clip_presence_sensor").state).to_be(STATE_OFF)
    expect(hass.states.get("binary_sensor.clip_flag_boot_time").state).to_be(STATE_ON)


@test
async def add_new_binary_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    send_sensor: Callable[[dict[str, Any]], Any] = Depends(sensor_ws_data),
) -> None:
    """Test that adding a new binary sensor works."""
    await setup_deconz(hass, aioclient)
    expect(len(hass.states.async_all())).to_be(0)

    event_added_sensor = {
        "e": "added",
        "sensor": {
            "id": "Presence sensor id",
            "name": "Presence sensor",
            "type": "ZHAPresence",
            "state": {"presence": False},
            "config": {"on": True, "reachable": True},
            "uniqueid": "00:00:00:00:00:00:00:00-00",
        },
    }
    await send_sensor(event_added_sensor)
    expect(len(hass.states.async_all())).to_be(1)
    expect(hass.states.get("binary_sensor.presence_sensor").state).to_be(STATE_OFF)


@test
async def add_new_binary_sensor_ignored_load_entities_on_service_call(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    send_sensor: Callable[[dict[str, Any]], Any] = Depends(sensor_ws_data),
) -> None:
    """Test that adding a new binary sensor is not allowed."""
    config_entry_setup = await setup_deconz(
        hass,
        aioclient,
        options={CONF_MASTER_GATEWAY: True, CONF_ALLOW_NEW_DEVICES: False},
    )

    sensor = {
        "name": "Presence sensor",
        "type": "ZHAPresence",
        "state": {"presence": False},
        "config": {"on": True, "reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    }

    expect(len(hass.states.async_all())).to_be(0)

    await send_sensor({"e": "added", "sensor": sensor})
    expect(len(hass.states.async_all())).to_be(0)
    expect(hass.states.get("binary_sensor.presence_sensor")).to_be(None)

    expect(
        len(
            er.async_entries_for_config_entry(
                entity_registry, config_entry_setup.entry_id
            )
        )
    ).to_be(0)

    # Re-register the get request with the new sensor in the payload.
    register_get_request(aioclient, sensor_payload=sensor)

    await hass.services.async_call(DOMAIN, SERVICE_DEVICE_REFRESH)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_be(1)
    expect(hass.states.get("binary_sensor.presence_sensor")).not_.to_be_none()


@test
async def add_new_binary_sensor_ignored_load_entities_on_options_change(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    send_sensor: Callable[[dict[str, Any]], Any] = Depends(sensor_ws_data),
) -> None:
    """Test that adding a new binary sensor is not allowed."""
    config_entry_setup = await setup_deconz(
        hass,
        aioclient,
        options={CONF_MASTER_GATEWAY: True, CONF_ALLOW_NEW_DEVICES: False},
    )

    sensor = {
        "name": "Presence sensor",
        "type": "ZHAPresence",
        "state": {"presence": False},
        "config": {"on": True, "reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    }

    expect(len(hass.states.async_all())).to_be(0)

    await send_sensor({"e": "added", "sensor": sensor})
    expect(len(hass.states.async_all())).to_be(0)
    expect(hass.states.get("binary_sensor.presence_sensor")).to_be(None)

    expect(
        len(
            er.async_entries_for_config_entry(
                entity_registry, config_entry_setup.entry_id
            )
        )
    ).to_be(0)

    register_get_request(aioclient, sensor_payload=sensor)

    hass.config_entries.async_update_entry(
        config_entry_setup, options={CONF_ALLOW_NEW_DEVICES: True}
    )
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_be(1)
    expect(hass.states.get("binary_sensor.presence_sensor")).not_.to_be_none()
