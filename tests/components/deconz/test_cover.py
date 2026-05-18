"""deCONZ cover platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    DOMAIN as COVER_DOMAIN,
    SERVICE_CLOSE_COVER,
    SERVICE_CLOSE_COVER_TILT,
    SERVICE_OPEN_COVER,
    SERVICE_OPEN_COVER_TILT,
    SERVICE_SET_COVER_POSITION,
    SERVICE_SET_COVER_TILT_POSITION,
    SERVICE_STOP_COVER,
    SERVICE_STOP_COVER_TILT,
    CoverState,
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


@test
async def cover(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
    send_light: Callable[[dict[str, Any]], Any] = Depends(light_ws_data),
) -> None:
    """Test that all supported cover entities are created."""
    light_payload = {
        "0": {
            "name": "Window covering device",
            "type": "Window covering device",
            "state": {"lift": 100, "open": False, "reachable": True},
            "modelid": "lumi.curtain",
            "uniqueid": "00:00:00:00:00:00:00:01-00",
        },
        "1": {
            "name": "Unsupported cover",
            "type": "Not a cover",
            "state": {"reachable": True},
            "uniqueid": "00:00:00:00:00:00:00:02-00",
        },
    }
    await setup_deconz(hass, aioclient, light_payload=light_payload)

    # Event signals cover is open
    await send_light({"state": {"lift": 0, "open": True}})
    cover_state = hass.states.get("cover.window_covering_device")
    expect(cover_state.state).to_equal(CoverState.OPEN)
    expect(cover_state.attributes[ATTR_CURRENT_POSITION]).to_equal(100)

    # Verify service calls for cover
    aioclient_mock_put = put_request("/lights/0/state")

    # Service open cover
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: "cover.window_covering_device"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal({"open": True})

    # Service close cover
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: "cover.window_covering_device"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[2][2]).to_equal({"open": False})

    # Service set cover position
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: "cover.window_covering_device", ATTR_POSITION: 40},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[3][2]).to_equal({"lift": 60})

    # Service stop cover movement
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: "cover.window_covering_device"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[4][2]).to_equal({"stop": True})


@test
async def tilt_cover(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
) -> None:
    """Test that tilting a cover works."""
    light_payload = {
        "etag": "87269755b9b3a046485fdae8d96b252c",
        "lastannounced": None,
        "lastseen": "2020-08-01T16:22:05Z",
        "manufacturername": "AXIS",
        "modelid": "Gear",
        "name": "Covering device",
        "state": {
            "bri": 0,
            "lift": 0,
            "on": False,
            "open": True,
            "reachable": True,
            "tilt": 0,
        },
        "swversion": "100-5.3.5.1122",
        "type": "Window covering device",
        "uniqueid": "00:24:46:00:00:12:34:56-01",
    }
    await setup_deconz(hass, aioclient, light_payload=light_payload)

    # Verify service calls for tilting cover
    aioclient_mock_put = put_request("/lights/0/state")

    # Service set tilt cover
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_TILT_POSITION,
        {ATTR_ENTITY_ID: "cover.covering_device", ATTR_TILT_POSITION: 40},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal({"tilt": 60})

    # Service open tilt cover
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: "cover.covering_device"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[2][2]).to_equal({"tilt": 0})

    # Service close tilt cover
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER_TILT,
        {ATTR_ENTITY_ID: "cover.covering_device"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[3][2]).to_equal({"tilt": 100})

    # Service stop cover movement
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER_TILT,
        {ATTR_ENTITY_ID: "cover.covering_device"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[4][2]).to_equal({"stop": True})


@test
async def level_controllable_output_cover(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
) -> None:
    """Test that a level controllable output cover works."""
    light_payload = {
        "etag": "4cefc909134c8e99086b55273c2bde67",
        "hascolor": False,
        "lastannounced": "2022-08-08T12:06:18Z",
        "lastseen": "2022-08-14T14:22Z",
        "manufacturername": "Keen Home Inc",
        "modelid": "SV01-410-MP-1.0",
        "name": "Vent",
        "state": {
            "alert": "none",
            "bri": 242,
            "on": False,
            "reachable": True,
            "sat": 10,
        },
        "swversion": "0x00000012",
        "type": "Level controllable output",
        "uniqueid": "00:22:a3:00:00:00:00:00-01",
    }
    await setup_deconz(hass, aioclient, light_payload=light_payload)

    # Verify service calls for tilting cover
    aioclient_mock_put = put_request("/lights/0/state")

    # Service open cover
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: "cover.vent"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal({"on": False})

    # Service close cover
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: "cover.vent"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[2][2]).to_equal({"on": True})

    # Service set cover position
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: "cover.vent", ATTR_POSITION: 40},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[3][2]).to_equal({"bri": 152})

    # Service set tilt cover
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_TILT_POSITION,
        {ATTR_ENTITY_ID: "cover.vent", ATTR_TILT_POSITION: 40},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[4][2]).to_equal({"sat": 152})

    # Service open tilt cover
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: "cover.vent"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[5][2]).to_equal({"sat": 0})

    # Service close tilt cover
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER_TILT,
        {ATTR_ENTITY_ID: "cover.vent"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[6][2]).to_equal({"sat": 254})

    # Service stop cover movement
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER_TILT,
        {ATTR_ENTITY_ID: "cover.vent"},
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[7][2]).to_equal({"bri_inc": 0})
