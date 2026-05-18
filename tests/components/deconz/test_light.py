"""deCONZ light platform tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.deconz.const import CONF_ALLOW_DECONZ_GROUPS
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_FLASH,
    ATTR_HS_COLOR,
    ATTR_SUPPORTED_COLOR_MODES,
    ATTR_TRANSITION,
    ATTR_XY_COLOR,
    DOMAIN as LIGHT_DOMAIN,
    EFFECT_COLORLOOP,
    FLASH_LONG,
    FLASH_SHORT,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    ColorMode,
    LightEntityFeature,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    STATE_OFF,
    STATE_ON,
)
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
def mock_websocket_data(
    mock_websocket: Any = Depends(mock_websocket_fixture),
) -> Callable[[dict[str, Any]], Any]:
    """Return a callable that sends generic websocket events."""

    async def send(data: dict[str, Any]) -> None:
        payload = dict(data)
        payload.setdefault("t", "event")
        payload.setdefault("e", "changed")
        payload.setdefault("id", "0")
        await mock_websocket(data=payload)

    return send


HUE_GO_LIGHT_PAYLOAD: dict[str, Any] = {
    "colorcapabilities": 31,
    "ctmax": 500,
    "ctmin": 153,
    "etag": "055485a82553e654f156d41c9301b7cf",
    "hascolor": True,
    "lastannounced": None,
    "lastseen": "2021-06-10T20:25Z",
    "manufacturername": "Philips",
    "modelid": "LLC020",
    "name": "Hue Go",
    "state": {
        "alert": "none",
        "bri": 254,
        "colormode": "ct",
        "ct": 375,
        "effect": "none",
        "hue": 8348,
        "on": True,
        "reachable": True,
        "sat": 147,
        "xy": [0.462, 0.4111],
    },
    "swversion": "5.127.1.26420",
    "type": "Extended color light",
    "uniqueid": "00:17:88:01:01:23:45:67-00",
}


@test.skip("snapshot test - port deferred")
async def lights() -> None:
    """Stub for test_lights (snapshot test)."""


@test
async def light_state_change(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    send_light: Callable[[dict[str, Any]], Any] = Depends(light_ws_data),
) -> None:
    """Verify light can change state on websocket event."""
    await setup_deconz(hass, aioclient, light_payload=dict(HUE_GO_LIGHT_PAYLOAD))

    expect(hass.states.get("light.hue_go").state).to_equal(STATE_ON)

    await send_light({"state": {"on": False}})
    expect(hass.states.get("light.hue_go").state).to_equal(STATE_OFF)


def _hue_go_payload(on: bool) -> dict[str, Any]:
    """Return a Hue Go light payload with the requested on state."""
    payload = dict(HUE_GO_LIGHT_PAYLOAD)
    payload["state"] = dict(HUE_GO_LIGHT_PAYLOAD["state"])
    payload["state"]["on"] = on
    return payload


@test.cases(
    test.case(
        "turn_on_with_hs_color",
        light_on=True,
        service=SERVICE_TURN_ON,
        call={
            ATTR_ENTITY_ID: "light.hue_go",
            ATTR_HS_COLOR: (20, 30),
        },
        expected={
            "on": True,
            "xy": (0.411, 0.351),
        },
    ),
    test.case(
        "turn_on_with_xy_color",
        light_on=True,
        service=SERVICE_TURN_ON,
        call={
            ATTR_ENTITY_ID: "light.hue_go",
            ATTR_XY_COLOR: (0.411, 0.351),
        },
        expected={
            "on": True,
            "xy": (0.411, 0.351),
        },
    ),
    test.case(
        "turn_on_no_transition",
        light_on=True,
        service=SERVICE_TURN_ON,
        call={
            ATTR_ENTITY_ID: "light.hue_go",
            ATTR_TRANSITION: 0,
        },
        expected={
            "on": True,
            "transitiontime": 0,
        },
    ),
    test.case(
        "turn_on_short_colorloop",
        light_on=False,
        service=SERVICE_TURN_ON,
        call={
            ATTR_ENTITY_ID: "light.hue_go",
            ATTR_BRIGHTNESS: 200,
            ATTR_COLOR_TEMP_KELVIN: 5000,
            ATTR_TRANSITION: 5,
            ATTR_FLASH: FLASH_SHORT,
            ATTR_EFFECT: EFFECT_COLORLOOP,
        },
        expected={
            "bri": 200,
            "ct": 200,
            "transitiontime": 50,
            "alert": "select",
            "effect": "colorloop",
        },
    ),
    test.case(
        "turn_on_disable_colorloop_long_flash",
        light_on=False,
        service=SERVICE_TURN_ON,
        call={
            ATTR_ENTITY_ID: "light.hue_go",
            ATTR_XY_COLOR: (0.411, 0.351),
            ATTR_FLASH: FLASH_LONG,
            ATTR_EFFECT: "none",
        },
        expected={
            "xy": (0.411, 0.351),
            "alert": "lselect",
            "effect": "none",
        },
    ),
    test.case(
        "turn_off_short_flash",
        light_on=True,
        service=SERVICE_TURN_OFF,
        call={
            ATTR_ENTITY_ID: "light.hue_go",
            ATTR_TRANSITION: 5,
            ATTR_FLASH: FLASH_SHORT,
        },
        expected={
            "bri": 0,
            "transitiontime": 50,
            "alert": "select",
        },
    ),
    test.case(
        "turn_off_no_transition",
        light_on=True,
        service=SERVICE_TURN_OFF,
        call={
            ATTR_ENTITY_ID: "light.hue_go",
            ATTR_TRANSITION: 0,
            ATTR_FLASH: FLASH_SHORT,
        },
        expected={
            "bri": 0,
            "transitiontime": 0,
            "alert": "select",
        },
    ),
    test.case(
        "turn_off_long_flash",
        light_on=True,
        service=SERVICE_TURN_OFF,
        call={ATTR_ENTITY_ID: "light.hue_go", ATTR_FLASH: FLASH_LONG},
        expected={"alert": "lselect"},
    ),
    test.case(
        "turn_off_when_already_off_not_supported",
        light_on=False,
        service=SERVICE_TURN_OFF,
        call={
            ATTR_ENTITY_ID: "light.hue_go",
            ATTR_TRANSITION: 5,
            ATTR_FLASH: FLASH_SHORT,
        },
        expected={},
    ),
)
async def light_service_calls(
    light_on: bool,
    service: str,
    call: dict[str, Any],
    expected: dict[str, Any],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
) -> None:
    """Verify light service calls produce the expected web requests."""
    await setup_deconz(hass, aioclient, light_payload=_hue_go_payload(light_on))

    aioclient_mock_put = put_request("/lights/0/state")

    await hass.services.async_call(
        LIGHT_DOMAIN,
        service,
        call,
        blocking=True,
    )
    if expected:
        expect(aioclient_mock_put.mock_calls[1][2]).to_equal(expected)
    else:
        expect(len(aioclient_mock_put.mock_calls)).to_equal(1)


@test
async def ikea_default_transition_time(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
) -> None:
    """Verify IKEA lights extend service calls with transitiontime 0 if absent."""
    light_payload = {
        "colorcapabilities": 0,
        "ctmax": 65535,
        "ctmin": 0,
        "etag": "9dd510cd474791481f189d2a68a3c7f1",
        "hascolor": True,
        "lastannounced": "2020-12-17T17:44:38Z",
        "lastseen": "2021-01-11T18:36Z",
        "manufacturername": "IKEA of Sweden",
        "modelid": "TRADFRI bulb E27 WS opal 1000lm",
        "name": "IKEA light",
        "state": {
            "alert": "none",
            "bri": 156,
            "colormode": "ct",
            "ct": 250,
            "on": True,
            "reachable": True,
        },
        "swversion": "2.0.022",
        "type": "Color temperature light",
        "uniqueid": "ec:1b:bd:ff:fe:ee:ed:dd-01",
    }
    await setup_deconz(hass, aioclient, light_payload=light_payload)

    aioclient_mock_put = put_request("/lights/0/state")

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.ikea_light",
            ATTR_BRIGHTNESS: 100,
        },
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal(
        {"bri": 100, "on": True, "transitiontime": 0}
    )

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.ikea_light",
            ATTR_BRIGHTNESS: 100,
            ATTR_TRANSITION: 5,
        },
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[2][2]).to_equal(
        {"bri": 100, "on": True, "transitiontime": 50}
    )


@test
async def lidl_christmas_light(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
) -> None:
    """Test that LIDL christmas light hs color is honored."""
    light_payload = {
        "etag": "87a89542bf9b9d0aa8134919056844f8",
        "hascolor": True,
        "lastannounced": None,
        "lastseen": "2020-12-05T22:57Z",
        "manufacturername": "_TZE200_s8gkrkxk",
        "modelid": "TS0601",
        "name": "LIDL xmas light",
        "state": {
            "bri": 25,
            "colormode": "hs",
            "effect": "none",
            "hue": 53691,
            "on": True,
            "reachable": True,
            "sat": 141,
        },
        "swversion": None,
        "type": "Color dimmable light",
        "uniqueid": "58:8e:81:ff:fe:db:7b:be-01",
    }
    await setup_deconz(hass, aioclient, light_payload=light_payload)

    aioclient_mock_put = put_request("/lights/0/state")

    await hass.services.async_call(
        LIGHT_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "light.lidl_xmas_light",
            ATTR_HS_COLOR: (20, 30),
        },
        blocking=True,
    )
    expect(aioclient_mock_put.mock_calls[1][2]).to_equal(
        {"on": True, "hue": 3640, "sat": 76}
    )
    expect(hass.states.get("light.lidl_xmas_light")).not_.to_be(None)


@test
async def configuration_tool(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Verify that configuration tool is not created as a light entity."""
    light_payload = {
        "etag": "26839cb118f5bf7ba1f2108256644010",
        "hascolor": False,
        "lastannounced": None,
        "lastseen": "2020-11-22T11:27Z",
        "manufacturername": "dresden elektronik",
        "modelid": "ConBee II",
        "name": "Configuration tool 1",
        "state": {"reachable": True},
        "swversion": "0x264a0700",
        "type": "Configuration tool",
        "uniqueid": "00:21:2e:ff:ff:05:a7:a3-01",
    }
    await setup_deconz(hass, aioclient, light_payload=light_payload)
    expect(len(hass.states.async_all())).to_equal(0)


@test.skip("snapshot test - port deferred")
async def groups() -> None:
    """Stub for test_groups (snapshot test)."""


GROUP_LIGHTS_PAYLOAD: dict[str, Any] = {
    "1": {
        "name": "RGB light",
        "state": {
            "bri": 255,
            "colormode": "xy",
            "effect": "colorloop",
            "hue": 53691,
            "on": True,
            "reachable": True,
            "sat": 141,
            "xy": (0.5, 0.5),
        },
        "type": "Extended color light",
        "uniqueid": "00:00:00:00:00:00:00:00-00",
    },
    "2": {
        "ctmax": 454,
        "ctmin": 155,
        "name": "Tunable white light",
        "state": {
            "on": True,
            "colormode": "ct",
            "ct": 2500,
            "reachable": True,
        },
        "type": "Tunable white light",
        "uniqueid": "00:00:00:00:00:00:00:01-00",
    },
    "3": {
        "name": "Dimmable light",
        "type": "Dimmable light",
        "state": {"bri": 254, "on": True, "reachable": True},
        "uniqueid": "00:00:00:00:00:00:00:02-00",
    },
}


@test.cases(
    test.case(
        "turn_on_short_colorloop",
        lights=["1", "2", "3"],
        group_on=False,
        service=SERVICE_TURN_ON,
        call={
            ATTR_ENTITY_ID: "light.group",
            ATTR_BRIGHTNESS: 200,
            ATTR_COLOR_TEMP_KELVIN: 5000,
            ATTR_TRANSITION: 5,
            ATTR_FLASH: FLASH_SHORT,
            ATTR_EFFECT: EFFECT_COLORLOOP,
        },
        expected={
            "bri": 200,
            "ct": 200,
            "transitiontime": 50,
            "alert": "select",
            "effect": "colorloop",
        },
    ),
    test.case(
        "turn_on_hs_colors",
        lights=["1", "2", "3"],
        group_on=False,
        service=SERVICE_TURN_ON,
        call={
            ATTR_ENTITY_ID: "light.group",
            ATTR_HS_COLOR: (250, 50),
        },
        expected={
            "on": True,
            "xy": (0.236, 0.166),
        },
    ),
    test.case(
        "turn_on_hs_colors_reordered_lights",
        lights=["3", "2", "1"],
        group_on=False,
        service=SERVICE_TURN_ON,
        call={
            ATTR_ENTITY_ID: "light.group",
            ATTR_HS_COLOR: (250, 50),
        },
        expected={
            "on": True,
            "xy": (0.236, 0.166),
        },
    ),
)
async def group_service_calls(
    lights: list[str],
    group_on: bool,
    service: str,
    call: dict[str, Any],
    expected: dict[str, Any],
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    put_request: Callable[[str, str], AiohttpClientMocker] = Depends(mock_put_request),
) -> None:
    """Verify expected group web request from different service calls."""
    group_payload = {
        "0": {
            "id": "Light group id",
            "name": "Group",
            "type": "LightGroup",
            "state": {"all_on": False, "any_on": group_on},
            "action": {},
            "scenes": [],
            "lights": lights,
        },
    }
    await setup_deconz(
        hass,
        aioclient,
        light_payload=GROUP_LIGHTS_PAYLOAD,
        group_payload=group_payload,
    )

    aioclient_mock_put = put_request("/groups/0/action")

    await hass.services.async_call(
        LIGHT_DOMAIN,
        service,
        call,
        blocking=True,
    )
    if expected:
        expect(aioclient_mock_put.mock_calls[1][2]).to_equal(expected)
    else:
        expect(len(aioclient_mock_put.mock_calls)).to_equal(1)


@test
async def empty_group(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Verify that a group without a list of lights is not created."""
    group_payload = {
        "0": {
            "id": "Empty group id",
            "name": "Empty group",
            "type": "LightGroup",
            "state": {},
            "action": {},
            "scenes": [],
            "lights": [],
        },
    }
    await setup_deconz(hass, aioclient, group_payload=group_payload)
    expect(len(hass.states.async_all())).to_equal(0)
    expect(hass.states.get("light.empty_group")).to_be(None)


@test
async def disable_light_groups(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test disallowing light groups work."""
    light_payload = {
        "ctmax": 454,
        "ctmin": 155,
        "name": "Tunable white light",
        "state": {"on": True, "colormode": "ct", "ct": 2500, "reachable": True},
        "type": "Tunable white light",
        "uniqueid": "00:00:00:00:00:00:00:01-00",
    }
    group_payload = {
        "1": {
            "id": "Light group id",
            "name": "Light group",
            "type": "LightGroup",
            "state": {"all_on": False, "any_on": True},
            "action": {},
            "scenes": [],
            "lights": ["0"],
        },
        "2": {
            "id": "Empty group id",
            "name": "Empty group",
            "type": "LightGroup",
            "state": {},
            "action": {},
            "scenes": [],
            "lights": [],
        },
    }
    config_entry = await setup_deconz(
        hass,
        aioclient,
        options={CONF_ALLOW_DECONZ_GROUPS: False},
        light_payload=light_payload,
        group_payload=group_payload,
    )

    expect(len(hass.states.async_all())).to_equal(1)
    expect(hass.states.get("light.tunable_white_light")).not_.to_be(None)
    expect(hass.states.get("light.light_group")).to_be(None)
    expect(hass.states.get("light.empty_group")).to_be(None)

    hass.config_entries.async_update_entry(
        config_entry, options={CONF_ALLOW_DECONZ_GROUPS: True}
    )
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(2)
    expect(hass.states.get("light.light_group")).not_.to_be(None)

    hass.config_entries.async_update_entry(
        config_entry, options={CONF_ALLOW_DECONZ_GROUPS: False}
    )
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(1)
    expect(hass.states.get("light.light_group")).to_be(None)


@test
async def non_color_light_reports_color(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    send_light: Callable[[dict[str, Any]], Any] = Depends(light_ws_data),
) -> None:
    """Verify hs_color does not crash when a group gets updated with a bad color."""
    light_payload = {
        "0": {
            "ctmax": 500,
            "ctmin": 153,
            "etag": "026bcfe544ad76c7534e5ca8ed39047c",
            "hascolor": True,
            "manufacturername": "dresden elektronik",
            "modelid": "FLS-PP3",
            "name": "Light 1",
            "pointsymbol": {},
            "state": {
                "alert": None,
                "bri": 111,
                "colormode": "ct",
                "ct": 307,
                "effect": None,
                "hascolor": True,
                "hue": 7998,
                "on": False,
                "reachable": True,
                "sat": 172,
                "xy": [0.421253, 0.39921],
            },
            "swversion": "020C.201000A0",
            "type": "Extended color light",
            "uniqueid": "00:21:2E:FF:FF:EE:DD:CC-0A",
        },
        "1": {
            "colorcapabilities": 0,
            "ctmax": 65535,
            "ctmin": 0,
            "etag": "9dd510cd474791481f189d2a68a3c7f1",
            "hascolor": True,
            "lastannounced": "2020-12-17T17:44:38Z",
            "lastseen": "2021-01-11T18:36Z",
            "manufacturername": "IKEA of Sweden",
            "modelid": "TRADFRI bulb E27 WS opal 1000lm",
            "name": "Küchenlicht",
            "state": {
                "alert": "none",
                "bri": 156,
                "colormode": "ct",
                "ct": 250,
                "on": True,
                "reachable": True,
            },
            "swversion": "2.0.022",
            "type": "Color temperature light",
            "uniqueid": "ec:1b:bd:ff:fe:ee:ed:dd-01",
        },
    }
    group_payload = {
        "0": {
            "action": {
                "alert": "none",
                "bri": 127,
                "colormode": "hs",
                "ct": 0,
                "effect": "none",
                "hue": 0,
                "on": True,
                "sat": 127,
                "scene": None,
                "xy": [0, 0],
            },
            "devicemembership": [],
            "etag": "81e42cf1b47affb72fa72bc2e25ba8bf",
            "lights": ["0", "1"],
            "name": "Group",
            "scenes": [],
            "state": {"all_on": False, "any_on": True},
            "type": "LightGroup",
        }
    }
    await setup_deconz(
        hass, aioclient, light_payload=light_payload, group_payload=group_payload
    )

    expect(len(hass.states.async_all())).to_equal(3)
    expect(hass.states.get("light.group").attributes[ATTR_SUPPORTED_COLOR_MODES]).to_equal(
        [ColorMode.COLOR_TEMP, ColorMode.HS, ColorMode.XY]
    )
    expect(hass.states.get("light.group").attributes[ATTR_COLOR_MODE]).to_equal(
        ColorMode.COLOR_TEMP
    )
    expect(hass.states.get("light.group").attributes[ATTR_COLOR_TEMP_KELVIN]).to_equal(
        4000
    )

    event_changed_light = {
        "id": "1",
        "state": {
            "alert": None,
            "bri": 216,
            "colormode": "xy",
            "ct": 410,
            "on": True,
            "reachable": True,
        },
        "uniqueid": "ec:1b:bd:ff:fe:ee:ed:dd-01",
    }
    await send_light(event_changed_light)
    group = hass.states.get("light.group")
    expect(group.attributes[ATTR_COLOR_MODE]).to_equal(ColorMode.XY)
    expect(group.attributes[ATTR_HS_COLOR]).to_equal((40.571, 41.176))
    expect(group.attributes.get(ATTR_COLOR_TEMP_KELVIN)).to_be(None)


@test
async def verify_group_supported_features(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test that group supported features reflect what included lights support."""
    light_payload = {
        "1": {
            "name": "Dimmable light",
            "state": {"on": True, "bri": 255, "reachable": True},
            "type": "Light",
            "uniqueid": "00:00:00:00:00:00:00:01-00",
        },
        "2": {
            "name": "Color light",
            "state": {
                "on": True,
                "bri": 100,
                "colormode": "xy",
                "effect": "colorloop",
                "xy": (500, 500),
                "reachable": True,
            },
            "type": "Extended color light",
            "uniqueid": "00:00:00:00:00:00:00:02-00",
        },
        "3": {
            "ctmax": 454,
            "ctmin": 155,
            "name": "Tunable light",
            "state": {"on": True, "colormode": "ct", "ct": 2500, "reachable": True},
            "type": "Tunable white light",
            "uniqueid": "00:00:00:00:00:00:00:03-00",
        },
    }
    group_payload = {
        "1": {
            "id": "Group1",
            "name": "Group",
            "type": "LightGroup",
            "state": {"all_on": False, "any_on": True},
            "action": {},
            "scenes": [],
            "lights": ["1", "2", "3"],
        },
    }
    await setup_deconz(
        hass, aioclient, light_payload=light_payload, group_payload=group_payload
    )

    expect(len(hass.states.async_all())).to_equal(4)

    group_state = hass.states.get("light.group")
    expect(group_state.state).to_equal(STATE_ON)
    expect(group_state.attributes[ATTR_COLOR_MODE]).to_equal(ColorMode.COLOR_TEMP)
    expect(group_state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(
        LightEntityFeature.TRANSITION
        | LightEntityFeature.FLASH
        | LightEntityFeature.EFFECT
    )


@test
async def verify_group_color_mode_fallback(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    send_ws: Callable[[dict[str, Any]], Any] = Depends(mock_websocket_data),
) -> None:
    """Test that group color mode falls back to brightness for dimmable lights."""
    light_payload = {
        "capabilities": {
            "alerts": [
                "none",
                "select",
                "lselect",
                "blink",
                "breathe",
                "okay",
                "channelchange",
                "finish",
                "stop",
            ],
            "bri": {"min_dim_level": 5},
        },
        "config": {
            "bri": {"execute_if_off": True, "startup": "previous"},
            "groups": ["43"],
            "on": {"startup": "previous"},
        },
        "etag": "ca0ed7763eca37f5e6b24f6d46f8a518",
        "hascolor": False,
        "lastannounced": None,
        "lastseen": "2024-03-02T20:08Z",
        "manufacturername": "Signify Netherlands B.V.",
        "modelid": "LWA001",
        "name": "Opbergruimte Lamp Plafond",
        "productid": "Philips-LWA001-1-A19DLv5",
        "productname": "Hue white lamp",
        "state": {
            "alert": "none",
            "bri": 76,
            "effect": "none",
            "on": False,
            "reachable": True,
        },
        "swconfigid": "87169548",
        "swversion": "1.104.2",
        "type": "Dimmable light",
        "uniqueid": "00:17:88:01:08:11:22:33-01",
    }
    group_payload = {
        "43": {
            "action": {
                "alert": "none",
                "bri": 127,
                "colormode": "hs",
                "ct": 0,
                "effect": "none",
                "hue": 0,
                "on": True,
                "sat": 127,
                "scene": "4",
                "xy": [0, 0],
            },
            "devicemembership": [],
            "etag": "4548e982c4cfff942f7af80958abb2a0",
            "id": "43",
            "lights": ["0"],
            "name": "Opbergruimte",
            "scenes": [
                {
                    "id": "1",
                    "lightcount": 1,
                    "name": "Scene Normaal deCONZ",
                    "transitiontime": 10,
                },
                {
                    "id": "2",
                    "lightcount": 1,
                    "name": "Scene Fel deCONZ",
                    "transitiontime": 10,
                },
                {
                    "id": "3",
                    "lightcount": 1,
                    "name": "Scene Gedimd deCONZ",
                    "transitiontime": 10,
                },
                {
                    "id": "4",
                    "lightcount": 1,
                    "name": "Scene Uit deCONZ",
                    "transitiontime": 10,
                },
            ],
            "state": {"all_on": False, "any_on": False},
            "type": "LightGroup",
        },
    }
    await setup_deconz(
        hass, aioclient, light_payload=light_payload, group_payload=group_payload
    )

    group_state = hass.states.get("light.opbergruimte")
    expect(group_state.state).to_equal(STATE_OFF)
    expect(group_state.attributes[ATTR_COLOR_MODE]).to_be(None)

    await send_ws(
        {
            "id": "0",
            "r": "lights",
            "state": {
                "alert": "none",
                "bri": 76,
                "effect": "none",
                "on": True,
                "reachable": True,
            },
            "uniqueid": "00:17:88:01:08:11:22:33-01",
        }
    )
    await send_ws(
        {
            "id": "43",
            "r": "groups",
            "state": {"all_on": True, "any_on": True},
        }
    )
    group_state = hass.states.get("light.opbergruimte")
    expect(group_state.state).to_equal(STATE_ON)
    expect(group_state.attributes[ATTR_COLOR_MODE]).to_be(ColorMode.BRIGHTNESS)
