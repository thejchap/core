"""deCONZ siren platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.siren import ATTR_DURATION, DOMAIN as SIREN_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
)
from homeassistant.core import HomeAssistant

from tests.components.deconz._fixtures import (
    mock_put_request,
    mock_websocket as mock_websocket_fixture,
    setup_deconz,
)
from tests.hass_fixtures import aioclient_mock, hass as hass_fixture, mock_network
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
async def sirens(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
    send_light: Callable[[dict[str, Any]], Any] = Depends(light_ws_data),
) -> None:
    """Test that siren entities are created."""
    light_payload = {
        "name": "Warning device",
        "type": "Warning device",
        "state": {"alert": "lselect", "reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    }
    await setup_deconz(hass, aioclient, light_payload=light_payload)

    expect(len(hass.states.async_all())).to_equal(1)
    expect(hass.states.get("siren.warning_device").state).to_equal(STATE_ON)

    await send_light({"state": {"alert": None}})
    expect(hass.states.get("siren.warning_device").state).to_equal(STATE_OFF)

    # Verify service calls

    aioclient_mock_put = put_request("/lights/0/state")

    # Service turn on siren

    await hass.services.async_call(
        SIREN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "siren.warning_device"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal({"alert": "lselect"})

    # Service turn off siren

    await hass.services.async_call(
        SIREN_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "siren.warning_device"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[2][2]).to_equal({"alert": "none"})

    # Service turn on siren with duration

    await hass.services.async_call(
        SIREN_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "siren.warning_device", ATTR_DURATION: 10},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[3][2]).to_equal(
        {"alert": "lselect", "ontime": 100}
    )
