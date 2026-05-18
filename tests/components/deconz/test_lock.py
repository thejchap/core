"""deCONZ lock platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.lock import (
    DOMAIN as LOCK_DOMAIN,
    SERVICE_LOCK,
    SERVICE_UNLOCK,
    LockState,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from tests.components.deconz._fixtures import (
    mock_put_request,
    mock_websocket as mock_websocket_fixture,
    setup_deconz,
)
from tests.hass_fixtures import (
    aioclient_mock,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture for tryke fixture-injection."""
    return 0


@fixture
def light_ws_data(
    mock_websocket: Any = Depends(mock_websocket_fixture),
) -> Callable[[dict[str, Any]], Any]:
    """Return a callable that sends light websocket events."""

    async def send(data: dict[str, Any]) -> None:
        payload: dict[str, Any] = {"r": "lights"}
        payload.update(data)
        payload.setdefault("t", "event")
        payload.setdefault("e", "changed")
        payload.setdefault("id", "0")
        await mock_websocket(data=payload)

    return send


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


@test
async def lock_from_light(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
    send_light: Callable[[dict[str, Any]], Any] = Depends(light_ws_data),
) -> None:
    """Test that all supported lock entities based on lights are created."""
    light_payload = {
        "etag": "5c2ec06cde4bd654aef3a555fcd8ad12",
        "hascolor": False,
        "lastannounced": None,
        "lastseen": "2020-08-22T15:29:03Z",
        "manufacturername": "Danalock",
        "modelid": "V3-BTZB",
        "name": "Door lock",
        "state": {"alert": "none", "on": False, "reachable": True},
        "swversion": "19042019",
        "type": "Door Lock",
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    }
    await setup_deconz(hass, aioclient, light_payload=light_payload)

    expect(len(hass.states.async_all())).to_equal(1)
    expect(hass.states.get("lock.door_lock").state).to_equal(LockState.UNLOCKED)

    await send_light({"state": {"on": True}})
    expect(hass.states.get("lock.door_lock").state).to_equal(LockState.LOCKED)

    # Verify service calls
    aioclient_mock_put = put_request("/lights/0/state")

    # Service lock door
    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_LOCK,
        {ATTR_ENTITY_ID: "lock.door_lock"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal({"on": True})

    # Service unlock door
    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_UNLOCK,
        {ATTR_ENTITY_ID: "lock.door_lock"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[2][2]).to_equal({"on": False})


@test
async def lock_from_sensor(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
    send_sensor: Callable[[dict[str, Any]], Any] = Depends(sensor_ws_data),
) -> None:
    """Test that all supported lock entities based on sensors are created."""
    sensor_payload = {
        "config": {
            "battery": 100,
            "lock": False,
            "on": True,
            "reachable": True,
        },
        "ep": 11,
        "etag": "a43862f76b7fa48b0fbb9107df123b0e",
        "lastseen": "2021-03-06T22:25Z",
        "manufacturername": "Onesti Products AS",
        "modelid": "easyCodeTouch_v1",
        "name": "Door lock",
        "state": {
            "lastupdated": "2021-03-06T21:25:45.624",
            "lockstate": "unlocked",
        },
        "swversion": "20201211",
        "type": "ZHADoorLock",
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    }
    await setup_deconz(hass, aioclient, sensor_payload=sensor_payload)

    expect(len(hass.states.async_all())).to_equal(2)
    expect(hass.states.get("lock.door_lock").state).to_equal(LockState.UNLOCKED)

    await send_sensor({"state": {"lockstate": "locked"}})
    expect(hass.states.get("lock.door_lock").state).to_equal(LockState.LOCKED)

    # Verify service calls
    aioclient_mock_put = put_request("/sensors/0/config")

    # Service lock door
    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_LOCK,
        {ATTR_ENTITY_ID: "lock.door_lock"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal({"lock": True})

    # Service unlock door
    await hass.services.async_call(
        LOCK_DOMAIN,
        SERVICE_UNLOCK,
        {ATTR_ENTITY_ID: "lock.door_lock"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[2][2]).to_equal({"lock": False})
