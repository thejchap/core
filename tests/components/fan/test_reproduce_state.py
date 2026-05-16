"""Test reproduce state for Fan."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.fan import (
    ATTR_DIRECTION,
    ATTR_OSCILLATING,
    ATTR_PERCENTAGE,
    ATTR_PRESET_MODE,
    ATTR_PRESET_MODES,
    DIRECTION_FORWARD,
    DIRECTION_REVERSE,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers.state import async_reproduce_state

from tests.common import async_mock_service
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    return 0


@fixture
async def _hass(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


MODERN_FAN_ENTITY = "fan.modern_fan"
MODERN_FAN_OFF_PERCENTAGE10_STATE = {
    ATTR_OSCILLATING: True,
    ATTR_DIRECTION: DIRECTION_FORWARD,
    ATTR_PERCENTAGE: 10,
    ATTR_PRESET_MODES: ["Auto", "Eco"],
}
MODERN_FAN_OFF_PERCENTAGE15_STATE = {
    ATTR_OSCILLATING: True,
    ATTR_DIRECTION: DIRECTION_FORWARD,
    ATTR_PERCENTAGE: 15,
    ATTR_PRESET_MODES: ["Auto", "Eco"],
}
MODERN_FAN_ON_INVALID_STATE = {
    ATTR_PRESET_MODES: ["Auto", "Eco"],
}
MODERN_FAN_OFF_PPRESET_MODE_AUTO_STATE = {
    ATTR_OSCILLATING: True,
    ATTR_DIRECTION: DIRECTION_FORWARD,
    ATTR_PRESET_MODE: "Auto",
    ATTR_PRESET_MODES: ["Auto", "Eco"],
}
MODERN_FAN_OFF_PPRESET_MODE_ECO_STATE = {
    ATTR_OSCILLATING: True,
    ATTR_DIRECTION: DIRECTION_FORWARD,
    ATTR_PRESET_MODE: "Eco",
    ATTR_PRESET_MODES: ["Auto", "Eco"],
}
MODERN_FAN_ON_PERCENTAGE10_STATE = {
    ATTR_OSCILLATING: True,
    ATTR_DIRECTION: DIRECTION_FORWARD,
    ATTR_PERCENTAGE: 10,
    ATTR_PRESET_MODES: ["Auto", "Eco"],
}
MODERN_FAN_ON_PERCENTAGE15_STATE = {
    ATTR_OSCILLATING: True,
    ATTR_DIRECTION: DIRECTION_FORWARD,
    ATTR_PERCENTAGE: 15,
    ATTR_PRESET_MODES: ["Auto", "Eco"],
}
MODERN_FAN_ON_PRESET_MODE_AUTO_STATE = {
    ATTR_OSCILLATING: True,
    ATTR_DIRECTION: DIRECTION_FORWARD,
    ATTR_PRESET_MODE: "Auto",
    ATTR_PRESET_MODES: ["Auto", "Eco"],
}
MODERN_FAN_ON_PRESET_MODE_ECO_STATE = {
    ATTR_OSCILLATING: True,
    ATTR_DIRECTION: DIRECTION_FORWARD,
    ATTR_PRESET_MODE: "Eco",
    ATTR_PRESET_MODES: ["Auto", "Eco"],
}
MODERN_FAN_PRESET_MODE_AUTO_REVERSE_STATE = {
    ATTR_OSCILLATING: True,
    ATTR_DIRECTION: DIRECTION_REVERSE,
    ATTR_PRESET_MODE: "Auto",
    ATTR_PRESET_MODES: ["Auto", "Eco"],
}


@test
async def reproducing_states(
    hass: HomeAssistant = Depends(_hass),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test reproducing Fan states."""
    hass.states.async_set("fan.entity_off", "off", {})
    hass.states.async_set("fan.entity_on", "on", {})
    hass.states.async_set("fan.entity_speed", "on", {"percentage": 100})
    hass.states.async_set("fan.entity_oscillating", "on", {"oscillating": True})
    hass.states.async_set("fan.entity_direction", "on", {"direction": "forward"})

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_calls = async_mock_service(hass, "fan", "set_percentage")

    # These calls should do nothing as entities already in desired state
    await async_reproduce_state(
        hass,
        [
            State("fan.entity_off", "off"),
            State("fan.entity_on", "on"),
            State("fan.entity_speed", "on", {"percentage": 100}),
            State("fan.entity_oscillating", "on", {"oscillating": True}),
            State("fan.entity_direction", "on", {"direction": "forward"}),
        ],
    )

    expect(len(turn_on_calls)).to_equal(0)
    expect(len(turn_off_calls)).to_equal(0)
    expect(len(set_direction_calls)).to_equal(0)
    expect(len(oscillate_calls)).to_equal(0)

    # Test invalid state is handled
    await async_reproduce_state(hass, [State("fan.entity_off", "not_supported")])

    expect("not_supported" in caplog.text).to_be(True)
    expect(len(turn_on_calls)).to_equal(0)
    expect(len(turn_off_calls)).to_equal(0)
    expect(len(set_direction_calls)).to_equal(0)
    expect(len(oscillate_calls)).to_equal(0)
    expect(len(set_percentage_calls)).to_equal(0)

    # Make sure correct services are called
    await async_reproduce_state(
        hass,
        [
            State("fan.entity_on", "off"),
            State("fan.entity_off", "on"),
            State("fan.entity_speed", "on", {"percentage": 25}),
            State("fan.entity_oscillating", "on", {"oscillating": False}),
            State("fan.entity_direction", "on", {"direction": "reverse"}),
            # Should not raise
            State("fan.non_existing", "on"),
        ],
    )

    expect(len(turn_on_calls)).to_equal(1)
    expect(turn_on_calls[0].domain).to_equal("fan")
    expect(turn_on_calls[0].data).to_equal({"entity_id": "fan.entity_off"})

    expect(len(set_direction_calls)).to_equal(1)
    expect(set_direction_calls[0].domain).to_equal("fan")
    expect(set_direction_calls[0].data).to_equal(
        {"entity_id": "fan.entity_direction", "direction": "reverse"}
    )

    expect(len(oscillate_calls)).to_equal(1)
    expect(oscillate_calls[0].domain).to_equal("fan")
    expect(oscillate_calls[0].data).to_equal(
        {"entity_id": "fan.entity_oscillating", "oscillating": False}
    )

    expect(len(set_percentage_calls)).to_equal(1)
    expect(set_percentage_calls[0].domain).to_equal("fan")
    expect(set_percentage_calls[0].data).to_equal(
        {"entity_id": "fan.entity_speed", "percentage": 25}
    )

    expect(len(turn_off_calls)).to_equal(1)
    expect(turn_off_calls[0].domain).to_equal("fan")
    expect(turn_off_calls[0].data).to_equal({"entity_id": "fan.entity_on"})


@test.cases(
    test.case("off_percentage10", start_state=MODERN_FAN_OFF_PERCENTAGE10_STATE),
    test.case("off_percentage15", start_state=MODERN_FAN_OFF_PERCENTAGE15_STATE),
    test.case("off_preset_auto", start_state=MODERN_FAN_OFF_PPRESET_MODE_AUTO_STATE),
    test.case("off_preset_eco", start_state=MODERN_FAN_OFF_PPRESET_MODE_ECO_STATE),
)
async def modern_turn_on_invalid(
    start_state: dict[str, Any],
    hass: HomeAssistant = Depends(_hass),
) -> None:
    """Test modern fan state reproduction, turning on with invalid state."""
    hass.states.async_set(MODERN_FAN_ENTITY, "off", start_state)

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_mode = async_mock_service(hass, "fan", "set_percentage")
    set_preset_mode = async_mock_service(hass, "fan", "set_preset_mode")

    # Turn on with an invalid config (speed, percentage, preset_modes all None)
    await async_reproduce_state(
        hass, [State(MODERN_FAN_ENTITY, "on", MODERN_FAN_ON_INVALID_STATE)]
    )

    expect(len(turn_on_calls)).to_equal(1)
    expect(turn_on_calls[0].domain).to_equal("fan")
    expect(turn_on_calls[0].data).to_equal({"entity_id": MODERN_FAN_ENTITY})

    expect(len(turn_off_calls)).to_equal(0)
    expect(len(set_direction_calls)).to_equal(1)
    expect(set_direction_calls[0].domain).to_equal("fan")
    expect(set_direction_calls[0].data).to_equal(
        {"entity_id": MODERN_FAN_ENTITY, ATTR_DIRECTION: None}
    )
    expect(len(oscillate_calls)).to_equal(1)
    expect(oscillate_calls[0].domain).to_equal("fan")
    expect(oscillate_calls[0].data).to_equal(
        {"entity_id": MODERN_FAN_ENTITY, ATTR_OSCILLATING: None}
    )
    expect(len(set_percentage_mode)).to_equal(0)
    expect(len(set_preset_mode)).to_equal(0)


@test.cases(
    test.case("off_percentage10", start_state=MODERN_FAN_OFF_PERCENTAGE10_STATE),
    test.case("off_preset_auto", start_state=MODERN_FAN_OFF_PPRESET_MODE_AUTO_STATE),
    test.case("off_preset_eco", start_state=MODERN_FAN_OFF_PPRESET_MODE_ECO_STATE),
)
async def modern_turn_on_percentage_from_different_speed(
    start_state: dict[str, Any],
    hass: HomeAssistant = Depends(_hass),
) -> None:
    """Test modern fan state reproduction, turning on with a different percentage of the state."""
    hass.states.async_set(MODERN_FAN_ENTITY, "off", start_state)

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_mode = async_mock_service(hass, "fan", "set_percentage")
    set_preset_mode = async_mock_service(hass, "fan", "set_preset_mode")

    await async_reproduce_state(
        hass, [State(MODERN_FAN_ENTITY, "on", MODERN_FAN_ON_PERCENTAGE15_STATE)]
    )

    expect(len(turn_on_calls)).to_equal(1)
    expect(turn_on_calls[0].domain).to_equal("fan")
    expect(turn_on_calls[0].data).to_equal(
        {"entity_id": MODERN_FAN_ENTITY, ATTR_PERCENTAGE: 15}
    )

    expect(len(turn_off_calls)).to_equal(0)
    expect(len(set_direction_calls)).to_equal(0)
    expect(len(oscillate_calls)).to_equal(0)
    expect(len(set_percentage_mode)).to_equal(0)
    expect(len(set_preset_mode)).to_equal(0)


@test
async def modern_turn_on_percentage_from_same_speed(
    hass: HomeAssistant = Depends(_hass),
) -> None:
    """Test modern fan state reproduction, turning on with the same percentage as in the state."""
    hass.states.async_set(MODERN_FAN_ENTITY, "off", MODERN_FAN_OFF_PERCENTAGE15_STATE)

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_mode = async_mock_service(hass, "fan", "set_percentage")
    set_preset_mode = async_mock_service(hass, "fan", "set_preset_mode")

    await async_reproduce_state(
        hass, [State(MODERN_FAN_ENTITY, "on", MODERN_FAN_ON_PERCENTAGE15_STATE)]
    )

    expect(len(turn_on_calls)).to_equal(1)
    expect(turn_on_calls[0].domain).to_equal("fan")
    expect(turn_on_calls[0].data).to_equal(
        {"entity_id": MODERN_FAN_ENTITY, ATTR_PERCENTAGE: 15}
    )

    expect(len(turn_off_calls)).to_equal(0)
    expect(len(set_direction_calls)).to_equal(0)
    expect(len(oscillate_calls)).to_equal(0)
    expect(len(set_percentage_mode)).to_equal(0)
    expect(len(set_preset_mode)).to_equal(0)


@test.cases(
    test.case("off_percentage10", start_state=MODERN_FAN_OFF_PERCENTAGE10_STATE),
    test.case("off_percentage15", start_state=MODERN_FAN_OFF_PERCENTAGE15_STATE),
    test.case("off_preset_eco", start_state=MODERN_FAN_OFF_PPRESET_MODE_ECO_STATE),
)
async def modern_turn_on_preset_mode_from_different_speed(
    start_state: dict[str, Any],
    hass: HomeAssistant = Depends(_hass),
) -> None:
    """Test modern fan state reproduction, turning on with a different preset mode from the state."""
    hass.states.async_set(MODERN_FAN_ENTITY, "off", start_state)

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_mode = async_mock_service(hass, "fan", "set_percentage")
    set_preset_mode = async_mock_service(hass, "fan", "set_preset_mode")

    await async_reproduce_state(
        hass, [State(MODERN_FAN_ENTITY, "on", MODERN_FAN_ON_PRESET_MODE_AUTO_STATE)]
    )

    expect(len(turn_on_calls)).to_equal(1)
    expect(turn_on_calls[0].domain).to_equal("fan")
    expect(turn_on_calls[0].data).to_equal(
        {"entity_id": MODERN_FAN_ENTITY, ATTR_PRESET_MODE: "Auto"}
    )

    expect(len(turn_off_calls)).to_equal(0)
    expect(len(set_direction_calls)).to_equal(0)
    expect(len(oscillate_calls)).to_equal(0)
    expect(len(set_percentage_mode)).to_equal(0)
    expect(len(set_preset_mode)).to_equal(0)


@test
async def modern_turn_on_preset_mode_from_same_speed(
    hass: HomeAssistant = Depends(_hass),
) -> None:
    """Test modern fan state reproduction, turning on with the same preset mode as in the state."""
    hass.states.async_set(
        MODERN_FAN_ENTITY, "off", MODERN_FAN_OFF_PPRESET_MODE_AUTO_STATE
    )

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_mode = async_mock_service(hass, "fan", "set_percentage")
    set_preset_mode = async_mock_service(hass, "fan", "set_preset_mode")

    await async_reproduce_state(
        hass, [State(MODERN_FAN_ENTITY, "on", MODERN_FAN_ON_PRESET_MODE_AUTO_STATE)]
    )

    expect(len(turn_on_calls)).to_equal(1)
    expect(turn_on_calls[0].domain).to_equal("fan")
    expect(turn_on_calls[0].data).to_equal(
        {"entity_id": MODERN_FAN_ENTITY, ATTR_PRESET_MODE: "Auto"}
    )

    expect(len(turn_off_calls)).to_equal(0)
    expect(len(set_direction_calls)).to_equal(0)
    expect(len(oscillate_calls)).to_equal(0)
    expect(len(set_percentage_mode)).to_equal(0)
    expect(len(set_preset_mode)).to_equal(0)


@test.cases(
    test.case("off_percentage10", start_state=MODERN_FAN_OFF_PERCENTAGE10_STATE),
    test.case("off_percentage15", start_state=MODERN_FAN_OFF_PERCENTAGE15_STATE),
    test.case("off_preset_eco", start_state=MODERN_FAN_OFF_PPRESET_MODE_ECO_STATE),
)
async def modern_turn_on_preset_mode_reverse(
    start_state: dict[str, Any],
    hass: HomeAssistant = Depends(_hass),
) -> None:
    """Test modern fan state reproduction, turning on with preset mode "Auto" and reverse direction."""
    hass.states.async_set(MODERN_FAN_ENTITY, "off", start_state)

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_mode = async_mock_service(hass, "fan", "set_percentage")
    set_preset_mode = async_mock_service(hass, "fan", "set_preset_mode")

    await async_reproduce_state(
        hass,
        [State(MODERN_FAN_ENTITY, "on", MODERN_FAN_PRESET_MODE_AUTO_REVERSE_STATE)],
    )

    expect(len(turn_on_calls)).to_equal(1)
    expect(turn_on_calls[0].domain).to_equal("fan")
    expect(turn_on_calls[0].data).to_equal(
        {"entity_id": MODERN_FAN_ENTITY, ATTR_PRESET_MODE: "Auto"}
    )
    expect(len(set_direction_calls)).to_equal(1)
    expect(set_direction_calls[0].domain).to_equal("fan")
    expect(set_direction_calls[0].data).to_equal(
        {"entity_id": MODERN_FAN_ENTITY, ATTR_DIRECTION: DIRECTION_REVERSE}
    )

    expect(len(turn_off_calls)).to_equal(0)
    expect(len(oscillate_calls)).to_equal(0)
    expect(len(set_percentage_mode)).to_equal(0)
    expect(len(set_preset_mode)).to_equal(0)


@test.cases(
    test.case("on_percentage10", start_state=MODERN_FAN_ON_PERCENTAGE10_STATE),
    test.case("on_percentage15", start_state=MODERN_FAN_ON_PERCENTAGE15_STATE),
    test.case("on_preset_eco", start_state=MODERN_FAN_ON_PRESET_MODE_ECO_STATE),
)
async def modern_to_preset(
    start_state: dict[str, Any],
    hass: HomeAssistant = Depends(_hass),
) -> None:
    """Test modern fan state reproduction, switching to preset mode "Auto"."""
    hass.states.async_set(MODERN_FAN_ENTITY, "on", start_state)

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_mode = async_mock_service(hass, "fan", "set_percentage")
    set_preset_mode = async_mock_service(hass, "fan", "set_preset_mode")

    await async_reproduce_state(
        hass, [State(MODERN_FAN_ENTITY, "on", MODERN_FAN_ON_PRESET_MODE_AUTO_STATE)]
    )

    expect(len(turn_on_calls)).to_equal(0)
    expect(len(turn_off_calls)).to_equal(0)
    expect(len(set_direction_calls)).to_equal(0)
    expect(len(oscillate_calls)).to_equal(0)
    expect(len(set_percentage_mode)).to_equal(0)
    expect(len(set_preset_mode)).to_equal(1)
    expect(set_preset_mode[0].domain).to_equal("fan")
    expect(set_preset_mode[0].data).to_equal(
        {"entity_id": MODERN_FAN_ENTITY, ATTR_PRESET_MODE: "Auto"}
    )


@test.cases(
    test.case("on_percentage10", start_state=MODERN_FAN_ON_PERCENTAGE10_STATE),
    test.case("on_preset_auto", start_state=MODERN_FAN_ON_PRESET_MODE_AUTO_STATE),
    test.case("on_preset_eco", start_state=MODERN_FAN_ON_PRESET_MODE_ECO_STATE),
)
async def modern_to_percentage(
    start_state: dict[str, Any],
    hass: HomeAssistant = Depends(_hass),
) -> None:
    """Test modern fan state reproduction, switching to 15% speed."""
    hass.states.async_set(MODERN_FAN_ENTITY, "on", start_state)

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_mode = async_mock_service(hass, "fan", "set_percentage")
    set_preset_mode = async_mock_service(hass, "fan", "set_preset_mode")

    await async_reproduce_state(
        hass, [State(MODERN_FAN_ENTITY, "on", MODERN_FAN_ON_PERCENTAGE15_STATE)]
    )

    expect(len(turn_on_calls)).to_equal(0)
    expect(len(turn_off_calls)).to_equal(0)
    expect(len(set_direction_calls)).to_equal(0)
    expect(len(oscillate_calls)).to_equal(0)
    expect(len(set_percentage_mode)).to_equal(1)
    expect(set_percentage_mode[0].domain).to_equal("fan")
    expect(set_percentage_mode[0].data).to_equal(
        {"entity_id": MODERN_FAN_ENTITY, ATTR_PERCENTAGE: 15}
    )
    expect(len(set_preset_mode)).to_equal(0)


@test
async def modern_direction(
    hass: HomeAssistant = Depends(_hass),
) -> None:
    """Test modern fan state reproduction, switching only direction state."""
    hass.states.async_set(MODERN_FAN_ENTITY, "on", MODERN_FAN_ON_PRESET_MODE_AUTO_STATE)

    turn_on_calls = async_mock_service(hass, "fan", "turn_on")
    turn_off_calls = async_mock_service(hass, "fan", "turn_off")
    set_direction_calls = async_mock_service(hass, "fan", "set_direction")
    oscillate_calls = async_mock_service(hass, "fan", "oscillate")
    set_percentage_mode = async_mock_service(hass, "fan", "set_percentage")
    set_preset_mode = async_mock_service(hass, "fan", "set_preset_mode")

    await async_reproduce_state(
        hass,
        [State(MODERN_FAN_ENTITY, "on", MODERN_FAN_PRESET_MODE_AUTO_REVERSE_STATE)],
    )

    expect(len(turn_on_calls)).to_equal(0)
    expect(len(turn_off_calls)).to_equal(0)
    expect(len(set_direction_calls)).to_equal(1)
    expect(set_direction_calls[0].domain).to_equal("fan")
    expect(set_direction_calls[0].data).to_equal(
        {"entity_id": MODERN_FAN_ENTITY, ATTR_DIRECTION: DIRECTION_REVERSE}
    )
    expect(len(oscillate_calls)).to_equal(0)
    expect(len(set_percentage_mode)).to_equal(0)
    expect(len(set_preset_mode)).to_equal(0)
