"""deCONZ scene platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.scene import (
    DOMAIN as SCENE_DOMAIN,
    SERVICE_TURN_ON,
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
def group_ws_data(
    mock_websocket: Any = Depends(mock_websocket_fixture),
) -> Callable[[dict[str, Any]], Any]:
    """Return a callable that sends group websocket events."""

    async def send(data: dict[str, Any]) -> None:
        payload: dict[str, Any] = {"r": "groups"}
        payload.update(data)
        payload.setdefault("t", "event")
        payload.setdefault("e", "changed")
        payload.setdefault("id", "1")
        await mock_websocket(data=payload)

    return send


@test
async def scenes(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
) -> None:
    """Test successful creation of scene entities."""
    group_payload = {
        "1": {
            "id": "Light group id",
            "name": "Light group",
            "type": "LightGroup",
            "state": {"all_on": False, "any_on": True},
            "action": {},
            "scenes": [{"id": "1", "name": "Scene"}],
            "lights": [],
        }
    }
    await setup_deconz(hass, aioclient, group_payload=group_payload)

    expect(hass.states.get("scene.light_group_scene")).not_.to_be_none()

    # Verify button press
    aioclient_mock_put = put_request("/groups/1/scenes/1/recall")

    await hass.services.async_call(
        SCENE_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "scene.light_group_scene"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal({})


@test
async def only_new_scenes_are_created(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    send_group: Callable[[dict[str, Any]], Any] = Depends(group_ws_data),
) -> None:
    """Test that scenes works."""
    group_payload = {
        "1": {
            "id": "Light group id",
            "name": "Light group",
            "type": "LightGroup",
            "state": {"all_on": False, "any_on": True},
            "action": {},
            "scenes": [{"id": "1", "name": "Scene"}],
            "lights": [],
        }
    }
    await setup_deconz(hass, aioclient, group_payload=group_payload)

    expect(len(hass.states.async_all())).to_equal(2)

    await send_group({"scenes": [{"id": "1", "name": "Scene"}]})

    expect(len(hass.states.async_all())).to_equal(2)
