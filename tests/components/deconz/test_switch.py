"""deCONZ switch platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.deconz.const import DOMAIN
from homeassistant.components.light import DOMAIN as LIGHT_DOMAIN
from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from tests.components.deconz._fixtures import (
    mock_put_request,
    mock_websocket as mock_websocket_fixture,
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
async def power_plugs(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
    send_light: Callable[[dict[str, Any]], Any] = Depends(light_ws_data),
) -> None:
    """Test that all supported switch entities are created."""
    light_payload = {
        "0": {
            "name": "On off switch",
            "type": "On/Off plug-in unit",
            "state": {"on": True, "reachable": True},
            "uniqueid": "00:00:00:00:00:00:00:00-00",
        },
        "1": {
            "name": "Smart plug",
            "type": "Smart plug",
            "state": {"on": False, "reachable": True},
            "uniqueid": "00:00:00:00:00:00:00:01-00",
        },
        "2": {
            "name": "Unsupported switch",
            "type": "Not a switch",
            "state": {"reachable": True},
            "uniqueid": "00:00:00:00:00:00:00:02-00",
        },
        "3": {
            "name": "On off relay",
            "state": {"on": True, "reachable": True},
            "type": "On/Off light",
            "uniqueid": "00:00:00:00:00:00:00:03-00",
        },
    }
    await setup_deconz(hass, aioclient, light_payload=light_payload)

    expect(len(hass.states.async_all())).to_equal(4)
    expect(hass.states.get("switch.on_off_switch").state).to_equal(STATE_ON)
    expect(hass.states.get("switch.smart_plug").state).to_equal(STATE_OFF)
    expect(hass.states.get("switch.on_off_relay").state).to_equal(STATE_ON)
    expect(hass.states.get("switch.unsupported_switch")).to_be_none()

    await send_light({"state": {"on": False}})
    expect(hass.states.get("switch.on_off_switch").state).to_equal(STATE_OFF)

    # Verify service calls
    aioclient_mock_put = put_request("/lights/0/state")

    # Service turn on power plug
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.on_off_switch"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal({"on": True})

    # Service turn off power plug
    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "switch.on_off_switch"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[2][2]).to_equal({"on": False})


@test
async def remove_legacy_on_off_output_as_light(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test that switch platform cleans up legacy light entities."""
    light_payload = {
        "name": "On Off output device",
        "type": "On/Off output",
        "state": {"on": True, "reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    }
    expect(
        entity_registry.async_get_or_create(
            LIGHT_DOMAIN, DOMAIN, "00:00:00:00:00:00:00:00-00"
        )
    ).to_be_truthy()

    await setup_deconz(hass, aioclient, light_payload=light_payload)

    expect(entity_registry.async_get("light.on_off_output_device")).to_be_none()
    expect(entity_registry.async_get("switch.on_off_output_device")).to_be_truthy()
    expect(len(hass.states.async_all())).to_equal(1)
