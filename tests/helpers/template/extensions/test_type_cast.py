"""Test type casting functions for Home Assistant templates."""

from __future__ import annotations

import math

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError

from tests.hass_fixtures import hass
from tests.helpers.template.helpers import render


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def float_function(hass: HomeAssistant = Depends(hass)) -> None:
    """Test float function."""
    hass.states.async_set("sensor.temperature", "12")

    expect(render(hass, "{{ float(states.sensor.temperature.state) }}")).to_equal(
        12.0
    )

    expect(
        render(hass, "{{ float(states.sensor.temperature.state) > 11 }}")
    ).to_be(True)

    # Test handling of invalid input
    expect(lambda: render(hass, "{{ float('forgiving') }}")).to_raise(TemplateError)

    # Test handling of default return value
    expect(render(hass, "{{ float('bad', 1) }}")).to_equal(1)
    expect(render(hass, "{{ float('bad', default=1) }}")).to_equal(1)


@test
async def float_filter(hass: HomeAssistant = Depends(hass)) -> None:
    """Test float filter."""
    hass.states.async_set("sensor.temperature", "12")

    expect(render(hass, "{{ states.sensor.temperature.state | float }}")).to_equal(
        12.0
    )
    expect(
        render(hass, "{{ states.sensor.temperature.state | float > 11 }}")
    ).to_be(True)

    # Test handling of invalid input
    expect(lambda: render(hass, "{{ 'bad' | float }}")).to_raise(TemplateError)

    # Test handling of default return value
    expect(render(hass, "{{ 'bad' | float(1) }}")).to_equal(1)
    expect(render(hass, "{{ 'bad' | float(default=1) }}")).to_equal(1)


@test
async def int_filter(hass: HomeAssistant = Depends(hass)) -> None:
    """Test int filter."""
    hass.states.async_set("sensor.temperature", "12.2")
    expect(render(hass, "{{ states.sensor.temperature.state | int }}")).to_equal(12)
    expect(
        render(hass, "{{ states.sensor.temperature.state | int > 11 }}")
    ).to_be(True)

    hass.states.async_set("sensor.temperature", "0x10")
    expect(
        render(hass, "{{ states.sensor.temperature.state | int(base=16) }}")
    ).to_equal(16)

    # Test handling of invalid input
    expect(lambda: render(hass, "{{ 'bad' | int }}")).to_raise(TemplateError)

    # Test handling of default return value
    expect(render(hass, "{{ 'bad' | int(1) }}")).to_equal(1)
    expect(render(hass, "{{ 'bad' | int(default=1) }}")).to_equal(1)


@test
async def int_function(hass: HomeAssistant = Depends(hass)) -> None:
    """Test int filter."""
    hass.states.async_set("sensor.temperature", "12.2")
    expect(render(hass, "{{ int(states.sensor.temperature.state) }}")).to_equal(12)
    expect(
        render(hass, "{{ int(states.sensor.temperature.state) > 11 }}")
    ).to_be(True)

    hass.states.async_set("sensor.temperature", "0x10")
    expect(
        render(hass, "{{ int(states.sensor.temperature.state, base=16) }}")
    ).to_equal(16)

    # Test handling of invalid input
    expect(lambda: render(hass, "{{ int('bad') }}")).to_raise(TemplateError)

    # Test handling of default return value
    expect(render(hass, "{{ int('bad', 1) }}")).to_equal(1)
    expect(render(hass, "{{ int('bad', default=1) }}")).to_equal(1)


@test
async def bool_function(hass: HomeAssistant = Depends(hass)) -> None:
    """Test bool function."""
    expect(render(hass, "{{ bool(true) }}")).to_be(True)
    expect(render(hass, "{{ bool(false) }}")).to_be(False)
    expect(render(hass, "{{ bool('on') }}")).to_be(True)
    expect(render(hass, "{{ bool('off') }}")).to_be(False)
    expect(lambda: render(hass, "{{ bool('unknown') }}")).to_raise(TemplateError)
    expect(lambda: render(hass, "{{ bool(none) }}")).to_raise(TemplateError)
    expect(render(hass, "{{ bool('unavailable', none) }}")).to_be(None)
    expect(render(hass, "{{ bool('unavailable', default=none) }}")).to_be(None)


@test
async def bool_filter(hass: HomeAssistant = Depends(hass)) -> None:
    """Test bool filter."""
    expect(render(hass, "{{ true | bool }}")).to_be(True)
    expect(render(hass, "{{ false | bool }}")).to_be(False)
    expect(render(hass, "{{ 'on' | bool }}")).to_be(True)
    expect(render(hass, "{{ 'off' | bool }}")).to_be(False)
    expect(lambda: render(hass, "{{ 'unknown' | bool }}")).to_raise(TemplateError)
    expect(lambda: render(hass, "{{ none | bool }}")).to_raise(TemplateError)
    expect(render(hass, "{{ 'unavailable' | bool(none) }}")).to_be(None)
    expect(render(hass, "{{ 'unavailable' | bool(default=none) }}")).to_be(None)


@test.cases(
    test.case("zero_int", value=0, expected=True),
    test.case("zero_float", value=0.0, expected=True),
    test.case("zero_str", value="0", expected=True),
    test.case("zero_float_str", value="0.0", expected=True),
    test.case("true", value=True, expected=True),
    test.case("false", value=False, expected=True),
    test.case("True_str", value="True", expected=False),
    test.case("False_str", value="False", expected=False),
    test.case("none", value=None, expected=False),
    test.case("None_str", value="None", expected=False),
    test.case("horse", value="horse", expected=False),
    test.case("pi", value=math.pi, expected=True),
    test.case("nan", value=math.nan, expected=False),
    test.case("inf", value=math.inf, expected=False),
    test.case("nan_str", value="nan", expected=False),
    test.case("inf_str", value="inf", expected=False),
)
async def isnumber(
    value: object,
    expected: bool,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test is_number."""
    expect(render(hass, "{{ is_number(value) }}", {"value": value})).to_equal(
        expected
    )
    expect(render(hass, "{{ value | is_number }}", {"value": value})).to_equal(
        expected
    )
    expect(render(hass, "{{ value is is_number }}", {"value": value})).to_equal(
        expected
    )


@test.cases(
    test.case("str", value="hello", expected=True),
    test.case("bytes", value=b"hello", expected=True),
    test.case("bytearray", value=bytearray(b"hello"), expected=True),
    test.case("int", value=42, expected=False),
    test.case("list", value=[1, 2], expected=False),
    test.case("none", value=None, expected=False),
)
async def string_like(
    value: object,
    expected: bool,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test string_like."""
    expect(render(hass, "{{ value is string_like }}", {"value": value})).to_equal(
        expected
    )
