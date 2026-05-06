"""Test string template extension."""

from __future__ import annotations

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant

from tests.hass_fixtures import hass
from tests.helpers.template.helpers import render


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def ordinal(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the ordinal filter."""
    tests = [
        (1, "1st"),
        (2, "2nd"),
        (3, "3rd"),
        (4, "4th"),
        (5, "5th"),
        (12, "12th"),
        (100, "100th"),
        (101, "101st"),
    ]

    for value, expected in tests:
        expect(render(hass, f"{{{{ {value} | ordinal }}}}")).to_equal(expected)


@test
async def slugify(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the slugify filter."""
    # Test as global function
    expect(render(hass, '{{ slugify("Home Assistant") }}')).to_equal("home_assistant")

    # Test as filter
    expect(render(hass, '{{ "Home Assistant" | slugify }}')).to_equal("home_assistant")

    # Test with custom separator as global
    expect(render(hass, '{{ slugify("Home Assistant", "-") }}')).to_equal(
        "home-assistant"
    )

    # Test with custom separator as filter
    expect(render(hass, '{{ "Home Assistant" | slugify("-") }}')).to_equal(
        "home-assistant"
    )


@test
async def urlencode(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the urlencode method."""
    # Test with dictionary

    result = render(
        hass, "{% set dict = {'foo': 'x&y', 'bar': 42} %}{{ dict | urlencode }}"
    )
    expect(result).to_equal("foo=x%26y&bar=42")

    # Test with string

    result = render(
        hass, "{% set string = 'the quick brown fox = true' %}{{ string | urlencode }}"
    )
    expect(result).to_equal("the%20quick%20brown%20fox%20%3D%20true")


@test
async def string_functions_with_non_string_input(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test string functions with non-string input (automatic conversion)."""
    # Test ordinal with integer
    expect(render(hass, "{{ 42 | ordinal }}")).to_equal("42nd")

    # Test slugify with integer - Note: Jinja2 may return integer for simple cases
    result = render(hass, "{{ 123 | slugify }}")
    # Accept either string or integer result for simple numeric cases
    expect(result in ["123", 123]).to_be(True)


@test
async def ordinal_edge_cases(hass: HomeAssistant = Depends(hass)) -> None:
    """Test ordinal function with edge cases."""
    # Test teens (11th, 12th, 13th should all be 'th')
    teens_tests = [
        (11, "11th"),
        (12, "12th"),
        (13, "13th"),
        (111, "111th"),
        (112, "112th"),
        (113, "113th"),
    ]

    for value, expected in teens_tests:
        expect(render(hass, f"{{{{ {value} | ordinal }}}}")).to_equal(expected)

    # Test other numbers ending in 1, 2, 3
    other_tests = [
        (21, "21st"),
        (22, "22nd"),
        (23, "23rd"),
        (121, "121st"),
        (122, "122nd"),
        (123, "123rd"),
    ]

    for value, expected in other_tests:
        expect(render(hass, f"{{{{ {value} | ordinal }}}}")).to_equal(expected)


@test
async def slugify_various_separators(hass: HomeAssistant = Depends(hass)) -> None:
    """Test slugify with various separators."""
    test_cases = [
        ("Hello World", "_", "hello_world"),
        ("Hello World", "-", "hello-world"),
        ("Hello World", ".", "hello.world"),
        ("Hello-World_Test", "~", "hello~world~test"),
    ]

    for text, separator, expected in test_cases:
        # Test as global function
        expect(
            render(hass, f'{{{{ slugify("{text}", "{separator}") }}}}')
        ).to_equal(expected)

        # Test as filter
        expect(
            render(hass, f'{{{{ "{text}" | slugify("{separator}") }}}}')
        ).to_equal(expected)


@test
async def urlencode_various_types(hass: HomeAssistant = Depends(hass)) -> None:
    """Test urlencode with various data types."""
    # Test with nested dictionary values
    result = render(
        hass,
        "{% set data = {'key': 'value with spaces', 'num': 123} %}{{ data | urlencode }}",
    )
    # URL encoding can have different order, so check both parts are present
    # Note: urllib.parse.urlencode uses + for spaces in form data
    expect("key=value+with+spaces" in result).to_be(True)
    expect("num=123" in result).to_be(True)

    # Test with special characters

    result = render(
        hass, "{% set data = {'special': 'a+b=c&d'} %}{{ data | urlencode }}"
    )
    expect(result).to_equal("special=a%2Bb%3Dc%26d")
