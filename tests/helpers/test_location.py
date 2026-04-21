"""Tests Home Assistant location helpers."""

from tryke import Depends, expect, fixture, test

from homeassistant.const import ATTR_FRIENDLY_NAME, ATTR_LATITUDE, ATTR_LONGITUDE
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import location

from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
def has_location_with_invalid_states() -> None:
    """Set up the tests."""
    for state in (None, 1, "hello", object):
        expect(location.has_location(state)).to_be(False)


@test
def has_location_with_states_with_invalid_locations() -> None:
    """Set up the tests."""
    state = State(
        "hello.world", "invalid", {ATTR_LATITUDE: "no number", ATTR_LONGITUDE: 123.12}
    )
    expect(location.has_location(state)).to_be(False)


@test
def has_location_with_states_with_valid_location() -> None:
    """Set up the tests."""
    state = State(
        "hello.world", "invalid", {ATTR_LATITUDE: 123.12, ATTR_LONGITUDE: 123.12}
    )
    expect(location.has_location(state)).to_be(True)


@test
def has_location_with_states_with_int_location() -> None:
    """Test that integer coordinates are valid."""
    state = State("hello.world", "valid", {ATTR_LATITUDE: 123, ATTR_LONGITUDE: 45})
    expect(location.has_location(state)).to_be(True)


@test
def closest_with_no_states_with_location() -> None:
    """Set up the tests."""
    state = State("light.test", "on")
    state2 = State(
        "light.test", "on", {ATTR_LATITUDE: "invalid", ATTR_LONGITUDE: 123.45}
    )
    state3 = State("light.test", "on", {ATTR_LONGITUDE: 123.45})

    expect(location.closest(123.45, 123.45, [state, state2, state3])).to_be_none()


@test
def closest_returns_closest() -> None:
    """Test ."""
    state = State("light.test", "on", {ATTR_LATITUDE: 124.45, ATTR_LONGITUDE: 124.45})
    state2 = State("light.test", "on", {ATTR_LATITUDE: 125.45, ATTR_LONGITUDE: 125.45})

    expect(location.closest(123.45, 123.45, [state, state2])).to_equal(state)


@test
async def coordinates_function_as_attributes(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test coordinates function."""
    hass.states.async_set(
        "test.object", "happy", {"latitude": 32.87336, "longitude": -117.22943}
    )
    expect(location.find_coordinates(hass, "test.object")).to_equal(
        "32.87336,-117.22943"
    )


@test
async def coordinates_function_as_state(hass: HomeAssistant = Depends(hass)) -> None:
    """Test coordinates function."""
    hass.states.async_set("test.object", "32.87336,-117.22943")
    expect(location.find_coordinates(hass, "test.object")).to_equal(
        "32.87336,-117.22943"
    )


@test
async def coordinates_function_device_tracker_in_zone(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test coordinates function."""
    hass.states.async_set(
        "zone.home",
        "zoning",
        {"latitude": 32.87336, "longitude": -117.22943},
    )
    hass.states.async_set("device_tracker.device", "home")
    expect(location.find_coordinates(hass, "device_tracker.device")).to_equal(
        "32.87336,-117.22943"
    )


@test
async def coordinates_function_zone_friendly_name(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test coordinates function."""
    hass.states.async_set(
        "zone.home",
        "zoning",
        {"latitude": 32.87336, "longitude": -117.22943, ATTR_FRIENDLY_NAME: "my_home"},
    )
    hass.states.async_set(
        "test.object",
        "my_home",
    )
    expect(location.find_coordinates(hass, "test.object")).to_equal(
        "32.87336,-117.22943"
    )
    expect(location.find_coordinates(hass, "my_home")).to_equal("32.87336,-117.22943")


@test
async def coordinates_function_device_tracker_from_input_select(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test coordinates function."""
    hass.states.async_set(
        "input_select.select",
        "device_tracker.device",
        {"options": "device_tracker.device"},
    )
    hass.states.async_set("device_tracker.device", "32.87336,-117.22943")
    expect(location.find_coordinates(hass, "input_select.select")).to_equal(
        "32.87336,-117.22943"
    )


@test
def coordinates_function_returns_none_on_recursion(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test coordinates function."""
    hass.states.async_set(
        "test.first",
        "test.second",
    )
    hass.states.async_set("test.second", "test.first")
    expect(location.find_coordinates(hass, "test.first")).to_be_none()


@test
async def coordinates_function_returns_state_if_no_coords(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test test_coordinates function."""
    hass.states.async_set(
        "test.object",
        "abc",
    )
    expect(location.find_coordinates(hass, "test.object")).to_equal("abc")


@test
def coordinates_function_returns_input_if_no_coords(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test test_coordinates function."""
    expect(location.find_coordinates(hass, "test.abc")).to_equal("test.abc")
    expect(location.find_coordinates(hass, "abc")).to_equal("abc")
