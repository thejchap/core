"""Test mathematical and statistical functions for Home Assistant templates."""

from __future__ import annotations

import math

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.template.extensions import MathExtension

from tests.hass_fixtures import hass
from tests.helpers.template.helpers import render


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def math_constants(hass: HomeAssistant = Depends(hass)) -> None:
    """Test math constants."""
    expect(render(hass, "{{ e }}")).to_equal(math.e)
    expect(render(hass, "{{ pi }}")).to_equal(math.pi)
    expect(render(hass, "{{ tau }}")).to_equal(math.pi * 2)


@test
async def logarithm(hass: HomeAssistant = Depends(hass)) -> None:
    """Test logarithm."""
    tests = [
        (4, 2, 2.0),
        (1000, 10, 3.0),
        (math.e, "", 1.0),  # The "" means the default base (e) will be used
    ]

    for value, base, expected in tests:
        expect(
            render(hass, f"{{{{ {value} | log({base}) | round(1) }}}}")
        ).to_equal(expected)
        expect(
            render(hass, f"{{{{ log({value}, {base}) | round(1) }}}}")
        ).to_equal(expected)

    # Test handling of invalid input
    expect(lambda: render(hass, "{{ invalid | log(_) }}")).to_raise(TemplateError)
    expect(lambda: render(hass, "{{ log(invalid, _) }}")).to_raise(TemplateError)
    expect(lambda: render(hass, "{{ 10 | log(invalid) }}")).to_raise(TemplateError)
    expect(lambda: render(hass, "{{ log(10, invalid) }}")).to_raise(TemplateError)

    # Test handling of default return value
    expect(render(hass, "{{ 'no_number' | log(10, 1) }}")).to_equal(1)
    expect(render(hass, "{{ 'no_number' | log(10, default=1) }}")).to_equal(1)
    expect(render(hass, "{{ log('no_number', 10, 1) }}")).to_equal(1)
    expect(render(hass, "{{ log('no_number', 10, default=1) }}")).to_equal(1)
    expect(render(hass, "{{ log(0, 10, 1) }}")).to_equal(1)
    expect(render(hass, "{{ log(0, 10, default=1) }}")).to_equal(1)


@test
async def sine(hass: HomeAssistant = Depends(hass)) -> None:
    """Test sine."""
    tests = [
        (0, 0.0),
        (math.pi / 2, 1.0),
        (math.pi, 0.0),
        (math.pi * 1.5, -1.0),
        (math.pi / 10, 0.309),
    ]

    for value, expected in tests:
        expect(render(hass, f"{{{{ {value} | sin | round(3) }}}}")).to_equal(expected)
        expect(render(hass, f"{{{{ sin({value}) | round(3) }}}}")).to_equal(expected)

    # Test handling of invalid input
    expect(lambda: render(hass, "{{ 'duck' | sin }}")).to_raise(TemplateError)
    expect(lambda: render(hass, "{{ invalid | sin('duck') }}")).to_raise(TemplateError)

    # Test handling of default return value
    expect(render(hass, "{{ 'no_number' | sin(1) }}")).to_equal(1)
    expect(render(hass, "{{ 'no_number' | sin(default=1) }}")).to_equal(1)
    expect(render(hass, "{{ sin('no_number', 1) }}")).to_equal(1)
    expect(render(hass, "{{ sin('no_number', default=1) }}")).to_equal(1)


@test
async def cosine(hass: HomeAssistant = Depends(hass)) -> None:
    """Test cosine."""
    tests = [
        (0, 1.0),
        (math.pi / 2, 0.0),
        (math.pi, -1.0),
        (math.pi * 1.5, 0.0),
        (math.pi / 3, 0.5),
    ]

    for value, expected in tests:
        expect(render(hass, f"{{{{ {value} | cos | round(3) }}}}")).to_equal(expected)
        expect(render(hass, f"{{{{ cos({value}) | round(3) }}}}")).to_equal(expected)

    expect(lambda: render(hass, "{{ 'duck' | cos }}")).to_raise(TemplateError)

    expect(render(hass, "{{ 'no_number' | cos(1) }}")).to_equal(1)
    expect(render(hass, "{{ 'no_number' | cos(default=1) }}")).to_equal(1)
    expect(render(hass, "{{ cos('no_number', 1) }}")).to_equal(1)
    expect(render(hass, "{{ cos('no_number', default=1) }}")).to_equal(1)


@test
async def tangent(hass: HomeAssistant = Depends(hass)) -> None:
    """Test tangent."""
    tests = [
        (0, 0.0),
        (math.pi / 4, 1.0),
        (math.pi, 0.0),
        (math.pi / 6, 0.577),
    ]

    for value, expected in tests:
        expect(render(hass, f"{{{{ {value} | tan | round(3) }}}}")).to_equal(expected)
        expect(render(hass, f"{{{{ tan({value}) | round(3) }}}}")).to_equal(expected)

    expect(lambda: render(hass, "{{ 'duck' | tan }}")).to_raise(TemplateError)

    expect(render(hass, "{{ 'no_number' | tan(1) }}")).to_equal(1)
    expect(render(hass, "{{ 'no_number' | tan(default=1) }}")).to_equal(1)
    expect(render(hass, "{{ tan('no_number', 1) }}")).to_equal(1)
    expect(render(hass, "{{ tan('no_number', default=1) }}")).to_equal(1)


@test
async def square_root(hass: HomeAssistant = Depends(hass)) -> None:
    """Test square root."""
    tests = [
        (0, 0.0),
        (1, 1.0),
        (4, 2.0),
        (9, 3.0),
        (16, 4.0),
        (0.25, 0.5),
    ]

    for value, expected in tests:
        expect(render(hass, f"{{{{ {value} | sqrt }}}}")).to_equal(expected)
        expect(render(hass, f"{{{{ sqrt({value}) }}}}")).to_equal(expected)

    expect(lambda: render(hass, "{{ 'duck' | sqrt }}")).to_raise(TemplateError)
    expect(lambda: render(hass, "{{ -1 | sqrt }}")).to_raise(TemplateError)

    expect(render(hass, "{{ 'no_number' | sqrt(1) }}")).to_equal(1)
    expect(render(hass, "{{ 'no_number' | sqrt(default=1) }}")).to_equal(1)
    expect(render(hass, "{{ sqrt('no_number', 1) }}")).to_equal(1)
    expect(render(hass, "{{ sqrt('no_number', default=1) }}")).to_equal(1)
    expect(render(hass, "{{ sqrt(-1, 1) }}")).to_equal(1)
    expect(render(hass, "{{ sqrt(-1, default=1) }}")).to_equal(1)


@test
async def arc_functions(hass: HomeAssistant = Depends(hass)) -> None:
    """Test arc trigonometric functions."""
    expect(render(hass, "{{ asin(0.5) | round(3) }}")).to_equal(
        round(math.asin(0.5), 3)
    )
    expect(render(hass, "{{ 0.5 | asin | round(3) }}")).to_equal(
        round(math.asin(0.5), 3)
    )

    expect(render(hass, "{{ acos(0.5) | round(3) }}")).to_equal(
        round(math.acos(0.5), 3)
    )
    expect(render(hass, "{{ 0.5 | acos | round(3) }}")).to_equal(
        round(math.acos(0.5), 3)
    )

    expect(render(hass, "{{ atan(1) | round(3) }}")).to_equal(round(math.atan(1), 3))
    expect(render(hass, "{{ 1 | atan | round(3) }}")).to_equal(round(math.atan(1), 3))

    expect(render(hass, "{{ atan2(1, 1) | round(3) }}")).to_equal(
        round(math.atan2(1, 1), 3)
    )
    expect(render(hass, "{{ atan2([1, 1]) | round(3) }}")).to_equal(
        round(math.atan2(1, 1), 3)
    )

    expect(lambda: render(hass, "{{ asin(2) }}")).to_raise(TemplateError)

    expect(render(hass, "{{ asin(2, 1) }}")).to_equal(1)
    expect(render(hass, "{{ acos(2, 1) }}")).to_equal(1)
    expect(render(hass, "{{ atan('invalid', 1) }}")).to_equal(1)
    expect(render(hass, "{{ atan2('invalid', 1, 1) }}")).to_equal(1)


@test
async def average(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the average function."""
    expect(render(hass, "{{ average([1, 2, 3]) }}")).to_equal(2)
    expect(render(hass, "{{ average(1, 2, 3) }}")).to_equal(2)

    expect(render(hass, "{{ average([1, 2, 3], -1) }}")).to_equal(2)
    expect(render(hass, "{{ average([], -1) }}")).to_equal(-1)
    expect(render(hass, "{{ average([], default=-1) }}")).to_equal(-1)
    expect(render(hass, "{{ average([], 5, default=-1) }}")).to_equal(-1)
    expect(render(hass, "{{ average(1, 'a', 3, default=-1) }}")).to_equal(-1)

    expect(lambda: render(hass, "{{ average() }}")).to_raise(TemplateError)
    expect(lambda: render(hass, "{{ average([]) }}")).to_raise(TemplateError)


@test
async def median(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the median function."""
    expect(render(hass, "{{ median([1, 2, 3]) }}")).to_equal(2)
    expect(render(hass, "{{ median([1, 2, 3, 4]) }}")).to_equal(2.5)
    expect(render(hass, "{{ median(1, 2, 3) }}")).to_equal(2)

    expect(render(hass, "{{ median([1, 2, 3], -1) }}")).to_equal(2)
    expect(render(hass, "{{ median([], -1) }}")).to_equal(-1)
    expect(render(hass, "{{ median([], default=-1) }}")).to_equal(-1)

    expect(lambda: render(hass, "{{ median() }}")).to_raise(TemplateError)
    expect(lambda: render(hass, "{{ median([]) }}")).to_raise(TemplateError)


@test
async def statistical_mode(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the statistical mode function."""
    expect(render(hass, "{{ statistical_mode([1, 1, 2, 3]) }}")).to_equal(1)
    expect(render(hass, "{{ statistical_mode(1, 1, 2, 3) }}")).to_equal(1)

    expect(render(hass, "{{ statistical_mode([1, 1, 2], -1) }}")).to_equal(1)
    expect(render(hass, "{{ statistical_mode([], -1) }}")).to_equal(-1)
    expect(render(hass, "{{ statistical_mode([], default=-1) }}")).to_equal(-1)

    expect(lambda: render(hass, "{{ statistical_mode() }}")).to_raise(TemplateError)
    expect(lambda: render(hass, "{{ statistical_mode([]) }}")).to_raise(TemplateError)


@test
async def min_max_functions(hass: HomeAssistant = Depends(hass)) -> None:
    """Test min and max functions."""
    expect(render(hass, "{{ min([1, 2, 3]) }}")).to_equal(1)
    expect(render(hass, "{{ min(1, 2, 3) }}")).to_equal(1)

    expect(render(hass, "{{ max([1, 2, 3]) }}")).to_equal(3)
    expect(render(hass, "{{ max(1, 2, 3) }}")).to_equal(3)

    expect(lambda: render(hass, "{{ min() }}")).to_raise(TemplateError)
    expect(lambda: render(hass, "{{ max() }}")).to_raise(TemplateError)


@test
async def bitwise_and(hass: HomeAssistant = Depends(hass)) -> None:
    """Test bitwise and."""
    expect(render(hass, "{{ bitwise_and(8, 2) }}")).to_equal(0)
    expect(render(hass, "{{ bitwise_and(10, 2) }}")).to_equal(2)
    expect(render(hass, "{{ bitwise_and(8, 8) }}")).to_equal(8)


@test
async def bitwise_or(hass: HomeAssistant = Depends(hass)) -> None:
    """Test bitwise or."""
    expect(render(hass, "{{ bitwise_or(8, 2) }}")).to_equal(10)
    expect(render(hass, "{{ bitwise_or(8, 8) }}")).to_equal(8)
    expect(render(hass, "{{ bitwise_or(10, 2) }}")).to_equal(10)


@test
async def bitwise_xor(hass: HomeAssistant = Depends(hass)) -> None:
    """Test bitwise xor."""
    expect(render(hass, "{{ bitwise_xor(8, 2) }}")).to_equal(10)
    expect(render(hass, "{{ bitwise_xor(8, 8) }}")).to_equal(0)
    expect(render(hass, "{{ bitwise_xor(10, 2) }}")).to_equal(8)


@test.cases(
    test.case("a", attribute="a"),
    test.case("b", attribute="b"),
    test.case("c", attribute="c"),
)
async def min_max_attribute(
    attribute: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the min and max filters with attribute."""
    hass.states.async_set(
        "test.object",
        "test",
        {
            "objects": [
                {"a": 1, "b": 2, "c": 3},
                {"a": 2, "b": 1, "c": 2},
                {"a": 3, "b": 3, "c": 1},
            ],
        },
    )
    expect(
        render(
            hass,
            f"{{{{ (state_attr('test.object', 'objects') | min(attribute='{attribute}'))['{attribute}']}}}}",
        )
    ).to_equal(1)
    expect(
        render(
            hass,
            f"{{{{ (min(state_attr('test.object', 'objects'), attribute='{attribute}'))['{attribute}']}}}}",
        )
    ).to_equal(1)
    expect(
        render(
            hass,
            f"{{{{ (state_attr('test.object', 'objects') | max(attribute='{attribute}'))['{attribute}']}}}}",
        )
    ).to_equal(3)
    expect(
        render(
            hass,
            f"{{{{ (max(state_attr('test.object', 'objects'), attribute='{attribute}'))['{attribute}']}}}}",
        )
    ).to_equal(3)


@test
async def clamp(hass: HomeAssistant = Depends(hass)) -> None:
    """Test clamp function."""
    expect(render(hass, "{{ clamp(15, 0, 10) }}")).to_equal(10.0)
    expect(render(hass, "{{ -5 | clamp(0, 10) }}")).to_equal(0.0)

    expect(MathExtension.clamp(5, 0, 10)).to_equal(5.0)
    expect(MathExtension.clamp(-5, 0, 10)).to_equal(0.0)
    expect(MathExtension.clamp(15, 0, 10)).to_equal(10.0)
    expect(MathExtension.clamp(0, 0, 10)).to_equal(0.0)
    expect(MathExtension.clamp(10, 0, 10)).to_equal(10.0)

    expect(MathExtension.clamp(5.5, 0, 10)).to_equal(5.5)
    expect(MathExtension.clamp(5.5, 0.5, 10.5)).to_equal(5.5)
    expect(MathExtension.clamp(0.25, 0.5, 10.5)).to_equal(0.5)
    expect(MathExtension.clamp(11.0, 0.5, 10.5)).to_equal(10.5)

    expect(MathExtension.clamp(-5, -10, -1)).to_equal(-5.0)
    expect(MathExtension.clamp(-15, -10, -1)).to_equal(-10.0)
    expect(MathExtension.clamp(0, -10, -1)).to_equal(-1.0)

    expect(MathExtension.clamp(5, 10, 10)).to_equal(10.0)

    for case in (
        "{{ clamp('invalid', 0, 10) }}",
        "{{ clamp(5, 'invalid', 10) }}",
        "{{ clamp(5, 0, 'invalid') }}",
    ):
        expect(lambda c=case: render(hass, c)).to_raise(TemplateError)


@test
async def wrap(hass: HomeAssistant = Depends(hass)) -> None:
    """Test wrap function."""
    expect(render(hass, "{{ wrap(15, 0, 10) }}")).to_equal(5.0)
    expect(render(hass, "{{ -5 | wrap(0, 10) }}")).to_equal(5.0)

    expect(MathExtension.wrap(5, 0, 10)).to_equal(5.0)
    expect(MathExtension.wrap(10, 0, 10)).to_equal(0.0)
    expect(MathExtension.wrap(15, 0, 10)).to_equal(5.0)
    expect(MathExtension.wrap(25, 0, 10)).to_equal(5.0)
    expect(MathExtension.wrap(-5, 0, 10)).to_equal(5.0)
    expect(MathExtension.wrap(-10, 0, 10)).to_equal(0.0)

    expect(MathExtension.wrap(370, 0, 360)).to_equal(10.0)
    expect(MathExtension.wrap(-10, 0, 360)).to_equal(350.0)
    expect(MathExtension.wrap(720, 0, 360)).to_equal(0.0)
    expect(MathExtension.wrap(361, 0, 360)).to_equal(1.0)

    expect(MathExtension.wrap(10.5, 0, 10)).to_equal(0.5)
    expect(MathExtension.wrap(370.5, 0, 360)).to_equal(10.5)

    expect(MathExtension.wrap(-15, -10, 0)).to_equal(-5.0)
    expect(MathExtension.wrap(5, -10, 0)).to_equal(-5.0)

    expect(MathExtension.wrap(25, 10, 20)).to_equal(15.0)
    expect(MathExtension.wrap(5, 10, 20)).to_equal(15.0)

    expect(MathExtension.wrap(5, 10, 10)).to_equal(10.0)

    for case in (
        "{{ wrap('invalid', 0, 10) }}",
        "{{ wrap(5, 'invalid', 10) }}",
        "{{ wrap(5, 0, 'invalid') }}",
    ):
        expect(lambda c=case: render(hass, c)).to_raise(TemplateError)


@test
async def remap(hass: HomeAssistant = Depends(hass)) -> None:
    """Test remap function."""
    # We don't check the return value; that's covered by the unit tests below.
    expect(bool(render(hass, "{{ remap(5, 0, 6, 0, 740, steps=10) }}"))).to_be(True)
    expect(bool(render(hass, "{{ 50 | remap(0, 100, 0, 10, steps=8) }}"))).to_be(True)

    expect(MathExtension.remap(0, 0, 10, 0, 100)).to_equal(0.0)
    expect(MathExtension.remap(5, 0, 10, 0, 100)).to_equal(50.0)
    expect(MathExtension.remap(10, 0, 10, 0, 100)).to_equal(100.0)

    expect(MathExtension.remap(50, 0, 100, 0, 10)).to_equal(5.0)
    expect(MathExtension.remap(25, 0, 100, 0, 10)).to_equal(2.5)

    expect(MathExtension.remap(0, -10, 10, 0, 100)).to_equal(50.0)
    expect(MathExtension.remap(-10, -10, 10, 0, 100)).to_equal(0.0)
    expect(MathExtension.remap(10, -10, 10, 0, 100)).to_equal(100.0)

    expect(MathExtension.remap(0, 0, 10, 100, 0)).to_equal(100.0)
    expect(MathExtension.remap(5, 0, 10, 100, 0)).to_equal(50.0)
    expect(MathExtension.remap(10, 0, 10, 100, 0)).to_equal(0.0)

    expect(MathExtension.remap(15, 0, 10, 0, 100, edges="none")).to_equal(150.0)
    expect(MathExtension.remap(-4, 0, 10, 0, 100, edges="none")).to_equal(-40.0)
    expect(MathExtension.remap(15, 0, 10, 0, 80, edges="clamp")).to_equal(80.0)
    expect(MathExtension.remap(-5, 0, 10, -1, 1, edges="clamp")).to_equal(-1)
    expect(MathExtension.remap(15, 0, 10, 0, 100, edges="wrap")).to_equal(50.0)
    expect(MathExtension.remap(-5, 0, 10, 0, 100, edges="wrap")).to_equal(50.0)

    expect(MathExtension.remap(0, 0, 100, 32, 212)).to_equal(32.0)
    expect(MathExtension.remap(100, 0, 100, 32, 212)).to_equal(212.0)
    expect(MathExtension.remap(50, 0, 100, 32, 212)).to_equal(122.0)

    expect(MathExtension.remap(80, 0, 60, 0, 360, edges="wrap")).to_equal(120.0)

    expect(MathExtension.remap(0, 0, 100, 0, 255)).to_equal(0.0)
    expect(MathExtension.remap(50, 0, 100, 0, 255)).to_equal(127.5)
    expect(MathExtension.remap(100, 0, 100, 0, 255)).to_equal(255.0)

    expect(MathExtension.remap(2.5, 0, 10, 0, 100)).to_equal(25.0)
    expect(MathExtension.remap(7.5, 0, 10, 0, 100)).to_equal(75.0)

    for case in (
        "{{ remap(5, 10, 10, 0, 100) }}",
        "{{ remap('invalid', 0, 10, 0, 100) }}",
        "{{ remap(5, 'invalid', 10, 0, 100) }}",
        "{{ remap(5, 0, 'invalid', 0, 100) }}",
        "{{ remap(5, 0, 10, 'invalid', 100) }}",
        "{{ remap(5, 0, 10, 0, 'invalid') }}",
    ):
        expect(lambda c=case: render(hass, c)).to_raise(TemplateError)


@test
async def remap_with_steps(hass: HomeAssistant = Depends(hass)) -> None:
    """Test remap function with steps parameter."""
    expect(MathExtension.remap(0.2, 0, 10, 0, 100, steps=10)).to_equal(0.0)
    expect(MathExtension.remap(5.3, 0, 10, 0, 100, steps=10)).to_equal(50.0)
    expect(MathExtension.remap(10, 0, 10, 0, 100, steps=10)).to_equal(100.0)

    expect(MathExtension.remap(2.4, 0, 10, 0, 100, steps=10)).to_equal(20.0)
    expect(MathExtension.remap(2.5, 0, 10, 0, 100, steps=10)).to_equal(20.0)
    expect(MathExtension.remap(2.6, 0, 10, 0, 100, steps=10)).to_equal(30.0)

    expect(MathExtension.remap(0, 0, 10, 0, 100, steps=4)).to_equal(0.0)
    expect(MathExtension.remap(2.5, 0, 10, 0, 100, steps=4)).to_equal(25.0)
    expect(MathExtension.remap(5, 0, 10, 0, 100, steps=4)).to_equal(50.0)
    expect(MathExtension.remap(7.5, 0, 10, 0, 100, steps=4)).to_equal(75.0)
    expect(MathExtension.remap(10, 0, 10, 0, 100, steps=4)).to_equal(100.0)

    expect(MathExtension.remap(2, 0, 10, 0, 100, steps=2)).to_equal(0.0)
    expect(MathExtension.remap(6, 0, 10, 0, 100, steps=2)).to_equal(50.0)
    expect(MathExtension.remap(8, 0, 10, 0, 100, steps=2)).to_equal(100.0)

    expect(MathExtension.remap(0, 0, 10, 0, 100, steps=1)).to_equal(0.0)
    expect(MathExtension.remap(5, 0, 10, 0, 100, steps=1)).to_equal(0.0)
    expect(MathExtension.remap(6, 0, 10, 0, 100, steps=1)).to_equal(100.0)
    expect(MathExtension.remap(10, 0, 10, 0, 100, steps=1)).to_equal(100.0)

    expect(MathExtension.remap(4.8, 0, 10, 100, 0, steps=4)).to_equal(50.0)

    expect(MathExtension.remap(5, 0, 10, 0, 100, steps=0)).to_equal(50.0)
    expect(MathExtension.remap(2.7, 0, 10, 0, 100, steps=0)).to_equal(27.0)
    expect(MathExtension.remap(5, 0, 10, 0, 100, steps=-1)).to_equal(50.0)


@test
async def remap_with_mirror(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the mirror edge mode of the remap function."""

    expect(
        [MathExtension.remap(i, 0, 4, 0, 1, edges="mirror") for i in range(-4, 9)]
    ).to_equal([1.0, 0.75, 0.5, 0.25, 0.0, 0.25, 0.5, 0.75, 1.0, 0.75, 0.5, 0.25, 0.0])

    expect(MathExtension.remap(15, 0, 10, 50, 150, edges="mirror")).to_equal(100.0)
    expect(MathExtension.remap(25, 0, 10, 50, 150, edges="mirror")).to_equal(100.0)
    expect(MathExtension.remap(15, 0, 10, 100, 0, edges="mirror")).to_equal(50.0)
    expect(MathExtension.remap(12, 0, 10, 100, 0, edges="mirror")).to_equal(20.0)
    # Approximate equality for float precision
    expect(
        abs(MathExtension.remap(-0.1, 0, 1, 0, 1, edges="mirror") - 0.1) < 1e-9
    ).to_be(True)


@test
async def rounding_value(hass: HomeAssistant = Depends(hass)) -> None:
    """Test rounding value."""
    hass.states.async_set("sensor.temperature", 12.78)

    expect(render(hass, "{{ states.sensor.temperature.state | round(1) }}")).to_equal(
        12.8
    )

    expect(
        render(hass, "{{ states.sensor.temperature.state | multiply(10) | round }}")
    ).to_equal(128)

    expect(
        render(hass, '{{ states.sensor.temperature.state | round(1, "floor") }}')
    ).to_equal(12.7)

    expect(
        render(hass, '{{ states.sensor.temperature.state | round(1, "ceil") }}')
    ).to_equal(12.8)

    expect(
        render(hass, '{{ states.sensor.temperature.state | round(1, "half") }}')
    ).to_equal(13.0)


@test
async def rounding_value_on_error(hass: HomeAssistant = Depends(hass)) -> None:
    """Test rounding value handling of error."""
    expect(lambda: render(hass, "{{ None | round }}")).to_raise(TemplateError)
    expect(lambda: render(hass, '{{ "no_number" | round }}')).to_raise(TemplateError)

    expect(render(hass, "{{ 'no_number' | round(default=1) }}")).to_equal(1)


@test
async def multiply(hass: HomeAssistant = Depends(hass)) -> None:
    """Test multiply."""
    tests = {10: 100}

    for inp, out in tests.items():
        expect(render(hass, f"{{{{ {inp} | multiply(10) | round }}}}")).to_equal(out)

    expect(lambda: render(hass, "{{ abcd | multiply(10) }}")).to_raise(TemplateError)

    expect(render(hass, "{{ 'no_number' | multiply(10, 1) }}")).to_equal(1)
    expect(render(hass, "{{ 'no_number' | multiply(10, default=1) }}")).to_equal(1)


@test
async def add(hass: HomeAssistant = Depends(hass)) -> None:
    """Test add."""
    tests = {10: 42}

    for inp, out in tests.items():
        expect(render(hass, f"{{{{ {inp} | add(32) | round }}}}")).to_equal(out)

    expect(lambda: render(hass, "{{ abcd | add(10) }}")).to_raise(TemplateError)

    expect(render(hass, "{{ 'no_number' | add(10, 1) }}")).to_equal(1)
    expect(render(hass, "{{ 'no_number' | add(10, default=1) }}")).to_equal(1)
