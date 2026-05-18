"""deCONZ number platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.number import (
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError

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
from tests.hass_tryke_helpers import expect_raises_async
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


PRESENCE_DELAY_PAYLOAD = {
    "name": "Presence sensor",
    "type": "ZHAPresence",
    "state": {"dark": False, "presence": False},
    "config": {
        "delay": 0,
        "on": True,
        "reachable": True,
        "temperature": 10,
    },
    "uniqueid": "00:00:00:00:00:00:00:00-00",
}

PRESENCE_DURATION_PAYLOAD = {
    "name": "Presence sensor",
    "type": "ZHAPresence",
    "state": {"dark": False, "presence": False},
    "config": {
        "duration": 0,
        "on": True,
        "reachable": True,
        "temperature": 10,
    },
    "uniqueid": "00:00:00:00:00:00:00:00-00",
}


@test.cases(
    test.case(
        "delay",
        sensor_payload=PRESENCE_DELAY_PAYLOAD,
        entity_id="number.presence_sensor_delay",
        websocket_event={"config": {"delay": 10}},
        next_state="10",
        supported_service_value=111,
        supported_service_response={"delay": 111},
        unsupported_service_value=0.1,
        unsupported_service_response={"delay": 0},
        out_of_range_service_value=66666,
    ),
    test.case(
        "duration",
        sensor_payload=PRESENCE_DURATION_PAYLOAD,
        entity_id="number.presence_sensor_duration",
        websocket_event={"config": {"duration": 10}},
        next_state="10",
        supported_service_value=111,
        supported_service_response={"duration": 111},
        unsupported_service_value=0.1,
        unsupported_service_response={"duration": 0},
        out_of_range_service_value=66666,
    ),
)
async def number_entities(
    sensor_payload: dict[str, Any],
    entity_id: str,
    websocket_event: dict[str, Any],
    next_state: str,
    supported_service_value: float,
    supported_service_response: dict[str, Any],
    unsupported_service_value: float,
    unsupported_service_response: dict[str, Any],
    out_of_range_service_value: float,
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
    send_sensor: Callable[[dict[str, Any]], Any] = Depends(sensor_ws_data),
) -> None:
    """Test successful creation of number entities."""
    await setup_deconz(hass, aioclient, sensor_payload=sensor_payload)

    expect(hass.states.get(entity_id)).not_.to_be_none()

    # Change state via websocket
    await send_sensor(websocket_event)
    expect(hass.states.get(entity_id).state).to_equal(next_state)

    # Verify service calls
    aioclient_mock_put = put_request("/sensors/0/config")

    # Service set supported value
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_VALUE: supported_service_value,
        },
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal(supported_service_response)

    # Service set float value (gets truncated to int)
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {
            ATTR_ENTITY_ID: entity_id,
            ATTR_VALUE: unsupported_service_value,
        },
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[2][2]).to_equal(unsupported_service_response)

    # Service set value beyond the supported range
    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {
                ATTR_ENTITY_ID: entity_id,
                ATTR_VALUE: out_of_range_service_value,
            },
            blocking=True,
        )
