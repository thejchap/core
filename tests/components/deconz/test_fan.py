"""deCONZ fan platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.fan import (
    ATTR_PERCENTAGE,
    DOMAIN as FAN_DOMAIN,
    SERVICE_SET_PERCENTAGE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
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


@test
async def fans(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
    send_light: Callable[[dict[str, Any]], Any] = Depends(light_ws_data),
) -> None:
    """Test that all supported fan entities are created."""
    light_payload = {
        "etag": "432f3de28965052961a99e3c5494daf4",
        "hascolor": False,
        "manufacturername": "King Of Fans,  Inc.",
        "modelid": "HDC52EastwindFan",
        "name": "Ceiling fan",
        "state": {
            "alert": "none",
            "bri": 254,
            "on": False,
            "reachable": True,
            "speed": 4,
        },
        "swversion": "0000000F",
        "type": "Fan",
        "uniqueid": "00:22:a3:00:00:27:8b:81-01",
    }
    await setup_deconz(hass, aioclient, light_payload=light_payload)

    # Test states
    for speed, percent in ((1, 25), (2, 50), (3, 75), (4, 100)):
        await send_light({"state": {"speed": speed}})
        expect(hass.states.get("fan.ceiling_fan").state).to_equal(STATE_ON)
        expect(
            hass.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE]
        ).to_equal(percent)

    await send_light({"state": {"speed": 0}})
    expect(hass.states.get("fan.ceiling_fan").state).to_equal(STATE_OFF)
    expect(hass.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE]).to_equal(0)

    # Test service calls
    aioclient_mock_put = put_request("/lights/0/state")

    # Service turn on fan using saved default_on_speed
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.ceiling_fan"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal({"speed": 4})

    # Service turn off fan
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "fan.ceiling_fan"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[2][2]).to_equal({"speed": 0})

    # Service turn on fan to 20%
    await hass.services.async_call(
        FAN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_PERCENTAGE: 20},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[3][2]).to_equal({"speed": 1})

    # Service set fan percentage
    for percent, speed in ((20, 1), (40, 2), (60, 3), (80, 4), (0, 0)):
        aioclient_mock_put.mock_calls.clear()
        await hass.services.async_call(
            FAN_DOMAIN,
            SERVICE_SET_PERCENTAGE,
            {ATTR_ENTITY_ID: "fan.ceiling_fan", ATTR_PERCENTAGE: percent},
            blocking=True,
        )
        expect(aioclient_mock_put.mock_calls[0][2]).to_equal({"speed": speed})

    # Events with an unsupported speed does not get converted
    await send_light({"state": {"speed": 5}})
    expect(hass.states.get("fan.ceiling_fan").state).to_equal(STATE_ON)
    expect(
        hass.states.get("fan.ceiling_fan").attributes[ATTR_PERCENTAGE]
    ).to_equal(None)
