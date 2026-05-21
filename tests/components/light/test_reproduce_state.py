"""Test reproduce state for Light (tryke port)."""

from tryke import Depends, expect, fixture, test

from homeassistant.components import light
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.state import async_reproduce_state

from tests.common import async_mock_service
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)

VALID_BRIGHTNESS = {"brightness": 180}
VALID_EFFECT = {"effect": "random"}
VALID_COLOR_TEMP_KELVIN = {"color_temp_kelvin": 4200}
VALID_HS_COLOR = {"hs_color": (345, 75)}
VALID_RGB_COLOR = {"rgb_color": (255, 63, 111)}
VALID_RGBW_COLOR = {"rgbw_color": (255, 63, 111, 10)}
VALID_RGBWW_COLOR = {"rgbww_color": (255, 63, 111, 10, 20)}
VALID_XY_COLOR = {"xy_color": (0.59, 0.274)}

NONE_BRIGHTNESS = {"brightness": None}
NONE_EFFECT = {"effect": None}
NONE_COLOR_TEMP_KELVIN = {"color_temp_kelvin": None}
NONE_HS_COLOR = {"hs_color": None}
NONE_RGB_COLOR = {"rgb_color": None}
NONE_RGBW_COLOR = {"rgbw_color": None}
NONE_RGBWW_COLOR = {"rgbww_color": None}
NONE_XY_COLOR = {"xy_color": None}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture for the module."""
    return hass


@test
async def reproducing_states(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test reproducing Light states."""
    hass.states.async_set("light.entity_off", "off", {})
    hass.states.async_set("light.entity_bright", "on", VALID_BRIGHTNESS)
    hass.states.async_set("light.entity_effect", "on", VALID_EFFECT)
    hass.states.async_set("light.entity_temp", "on", VALID_COLOR_TEMP_KELVIN)
    hass.states.async_set("light.entity_hs", "on", VALID_HS_COLOR)
    hass.states.async_set("light.entity_rgb", "on", VALID_RGB_COLOR)
    hass.states.async_set("light.entity_xy", "on", VALID_XY_COLOR)

    turn_on_calls = async_mock_service(hass, "light", "turn_on")
    turn_off_calls = async_mock_service(hass, "light", "turn_off")

    # These calls should do nothing as entities already in desired state
    await async_reproduce_state(
        hass,
        [
            State("light.entity_off", "off"),
            State("light.entity_bright", "on", VALID_BRIGHTNESS),
            State("light.entity_effect", "on", VALID_EFFECT),
            State("light.entity_temp", "on", VALID_COLOR_TEMP_KELVIN),
            State("light.entity_hs", "on", VALID_HS_COLOR),
            State("light.entity_rgb", "on", VALID_RGB_COLOR),
            State("light.entity_xy", "on", VALID_XY_COLOR),
        ],
    )

    expect(len(turn_on_calls)).to_be(0)
    expect(len(turn_off_calls)).to_be(0)

    # Test invalid state is handled
    await async_reproduce_state(hass, [State("light.entity_off", "not_supported")])

    expect("not_supported" in caplog.text).to_be(True)
    expect(len(turn_on_calls)).to_be(0)
    expect(len(turn_off_calls)).to_be(0)

    # Make sure correct services are called
    await async_reproduce_state(
        hass,
        [
            State("light.entity_xy", "off"),
            State("light.entity_off", "on", VALID_BRIGHTNESS),
            State("light.entity_bright", "on", VALID_EFFECT),
            State("light.entity_effect", "on", VALID_COLOR_TEMP_KELVIN),
            State("light.entity_temp", "on", VALID_HS_COLOR),
            State("light.entity_hs", "on", VALID_RGB_COLOR),
            State("light.entity_rgb", "on", VALID_XY_COLOR),
        ],
    )

    expect(len(turn_on_calls)).to_be(6)

    expected_calls = []

    expected_off = dict(VALID_BRIGHTNESS)
    expected_off["entity_id"] = "light.entity_off"
    expected_calls.append(expected_off)

    expected_bright = dict(VALID_EFFECT)
    expected_bright["entity_id"] = "light.entity_bright"
    expected_calls.append(expected_bright)

    expected_effect = dict(VALID_COLOR_TEMP_KELVIN)
    expected_effect["entity_id"] = "light.entity_effect"
    expected_calls.append(expected_effect)

    expected_temp = dict(VALID_HS_COLOR)
    expected_temp["entity_id"] = "light.entity_temp"
    expected_calls.append(expected_temp)

    expected_hs = dict(VALID_RGB_COLOR)
    expected_hs["entity_id"] = "light.entity_hs"
    expected_calls.append(expected_hs)

    expected_rgb = dict(VALID_XY_COLOR)
    expected_rgb["entity_id"] = "light.entity_rgb"
    expected_calls.append(expected_rgb)

    for call in turn_on_calls:
        expect(call.domain).to_be("light")
        found = False
        for expected in expected_calls:
            if call.data["entity_id"] == expected["entity_id"]:
                # We found the matching entry
                expect(call.data).to_equal(expected)
                found = True
                break
        # No entry found
        expect(found).to_be(True)

    expect(len(turn_off_calls)).to_be(1)
    expect(turn_off_calls[0].domain).to_be("light")
    expect(turn_off_calls[0].data).to_equal({"entity_id": "light.entity_xy"})


@test.cases(
    test.case("color_temp", color_mode=light.ColorMode.COLOR_TEMP),
    test.case("brightness", color_mode=light.ColorMode.BRIGHTNESS),
    test.case("hs", color_mode=light.ColorMode.HS),
    test.case("onoff", color_mode=light.ColorMode.ONOFF),
    test.case("rgb", color_mode=light.ColorMode.RGB),
    test.case("rgbw", color_mode=light.ColorMode.RGBW),
    test.case("rgbww", color_mode=light.ColorMode.RGBWW),
    test.case("unknown", color_mode=light.ColorMode.UNKNOWN),
    test.case("white", color_mode=light.ColorMode.WHITE),
    test.case("xy", color_mode=light.ColorMode.XY),
)
async def filter_color_modes(
    color_mode: light.ColorMode,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test filtering of parameters according to color mode."""
    hass.states.async_set("light.entity", "off", {})
    all_colors = {
        **VALID_COLOR_TEMP_KELVIN,
        **VALID_HS_COLOR,
        **VALID_RGB_COLOR,
        **VALID_RGBW_COLOR,
        **VALID_RGBWW_COLOR,
        **VALID_XY_COLOR,
        **VALID_BRIGHTNESS,
    }

    turn_on_calls = async_mock_service(hass, "light", "turn_on")

    await async_reproduce_state(
        hass, [State("light.entity", "on", {**all_colors, "color_mode": color_mode})]
    )

    expected_map = {
        light.ColorMode.COLOR_TEMP: {**VALID_BRIGHTNESS, **VALID_COLOR_TEMP_KELVIN},
        light.ColorMode.BRIGHTNESS: VALID_BRIGHTNESS,
        light.ColorMode.HS: {**VALID_BRIGHTNESS, **VALID_HS_COLOR},
        light.ColorMode.ONOFF: {**VALID_BRIGHTNESS},
        light.ColorMode.RGB: {**VALID_BRIGHTNESS, **VALID_RGB_COLOR},
        light.ColorMode.RGBW: {**VALID_BRIGHTNESS, **VALID_RGBW_COLOR},
        light.ColorMode.RGBWW: {**VALID_BRIGHTNESS, **VALID_RGBWW_COLOR},
        light.ColorMode.UNKNOWN: {
            **VALID_BRIGHTNESS,
            **VALID_HS_COLOR,
        },
        light.ColorMode.WHITE: {
            **VALID_BRIGHTNESS,
            light.ATTR_WHITE: VALID_BRIGHTNESS[light.ATTR_BRIGHTNESS],
        },
        light.ColorMode.XY: {**VALID_BRIGHTNESS, **VALID_XY_COLOR},
    }
    expected = expected_map[color_mode]

    expect(len(turn_on_calls)).to_be(1)
    expect(turn_on_calls[0].domain).to_be("light")
    expect(dict(turn_on_calls[0].data)).to_equal(
        {"entity_id": "light.entity", **expected}
    )

    # This should do nothing, the light is already in the desired state
    hass.states.async_set("light.entity", "on", {"color_mode": color_mode, **expected})
    await async_reproduce_state(
        hass, [State("light.entity", "on", {**expected, "color_mode": color_mode})]
    )
    expect(len(turn_on_calls)).to_be(1)


@test
async def filter_color_modes_missing_attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test warning on missing attribute when filtering for color mode."""
    color_mode = light.ColorMode.COLOR_TEMP
    hass.states.async_set("light.entity", "off", {})
    expected_log = (
        "Color mode color_temp specified "
        "but attribute color_temp_kelvin missing for: light.entity"
    )
    expected_fallback_log = "using color_temp (mireds) as fallback"

    turn_on_calls = async_mock_service(hass, "light", "turn_on")

    all_colors = {
        **VALID_COLOR_TEMP_KELVIN,
        **VALID_HS_COLOR,
        **VALID_RGB_COLOR,
        **VALID_RGBW_COLOR,
        **VALID_RGBWW_COLOR,
        **VALID_XY_COLOR,
        **VALID_BRIGHTNESS,
    }

    # Test missing `color_temp_kelvin` attribute
    stored_attributes = {**all_colors}
    stored_attributes.pop("color_temp_kelvin")
    caplog.clear()
    await async_reproduce_state(
        hass,
        [State("light.entity", "on", {**stored_attributes, "color_mode": color_mode})],
    )
    expect(len(turn_on_calls)).to_be(0)
    expect(expected_log in caplog.text).to_be(True)
    expect(expected_fallback_log in caplog.text).to_be(False)

    # Test with correct `color_temp_kelvin` attribute
    expected = {"brightness": 180, "color_temp_kelvin": 4200}
    caplog.clear()
    turn_on_calls.clear()
    await async_reproduce_state(
        hass,
        [State("light.entity", "on", {**all_colors, "color_mode": color_mode})],
    )
    expect(len(turn_on_calls)).to_be(1)
    expect(turn_on_calls[0].domain).to_be("light")
    expect(dict(turn_on_calls[0].data)).to_equal(
        {"entity_id": "light.entity", **expected}
    )
    expect(expected_log in caplog.text).to_be(False)
    expect(expected_fallback_log in caplog.text).to_be(False)


@test.cases(
    test.case("brightness", saved_state=NONE_BRIGHTNESS),
    test.case("effect", saved_state=NONE_EFFECT),
    test.case("color_temp_kelvin", saved_state=NONE_COLOR_TEMP_KELVIN),
    test.case("hs_color", saved_state=NONE_HS_COLOR),
    test.case("rgb_color", saved_state=NONE_RGB_COLOR),
    test.case("rgbw_color", saved_state=NONE_RGBW_COLOR),
    test.case("rgbww_color", saved_state=NONE_RGBWW_COLOR),
    test.case("xy_color", saved_state=NONE_XY_COLOR),
)
async def filter_none(
    saved_state: dict,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test filtering of parameters which are None."""
    hass.states.async_set("light.entity", "off", {})

    turn_on_calls = async_mock_service(hass, "light", "turn_on")

    await async_reproduce_state(hass, [State("light.entity", "on", saved_state)])

    expect(len(turn_on_calls)).to_be(1)
    expect(turn_on_calls[0].domain).to_be("light")
    expect(dict(turn_on_calls[0].data)).to_equal({"entity_id": "light.entity"})

    # This should do nothing, the light is already in the desired state
    hass.states.async_set("light.entity", "on", {})
    await async_reproduce_state(hass, [State("light.entity", "on", saved_state)])
    expect(len(turn_on_calls)).to_be(1)
