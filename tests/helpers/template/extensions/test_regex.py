"""Test regex template extension."""

from __future__ import annotations

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
async def regex_match(hass: HomeAssistant = Depends(hass)) -> None:
    """Test regex_match method."""

    result = render(
        hass, r"""{{ '123-456-7890' | regex_match('(\\d{3})-(\\d{3})-(\\d{4})') }}"""
    )
    expect(result).to_be(True)

    result = render(hass, """{{ 'Home Assistant test' | regex_match('home', True) }}""")
    expect(result).to_be(True)

    result = render(hass, """{{ 'Another Home Assistant test'|regex_match('Home') }}""")
    expect(result).to_be(False)

    result = render(hass, """{{ ['Home Assistant test'] | regex_match('.*Assist') }}""")
    expect(result).to_be(True)


@test
async def match_test(hass: HomeAssistant = Depends(hass)) -> None:
    """Test match test."""

    result = render(
        hass, r"""{{ '123-456-7890' is match('(\\d{3})-(\\d{3})-(\\d{4})') }}"""
    )
    expect(result).to_be(True)


@test
async def regex_search(hass: HomeAssistant = Depends(hass)) -> None:
    """Test regex_search method."""

    result = render(
        hass, r"""{{ '123-456-7890' | regex_search('(\\d{3})-(\\d{3})-(\\d{4})') }}"""
    )
    expect(result).to_be(True)

    result = render(
        hass, """{{ 'Home Assistant test' | regex_search('home', True) }}"""
    )
    expect(result).to_be(True)

    result = render(
        hass, """    {{ 'Another Home Assistant test' | regex_search('Home') }}"""
    )
    expect(result).to_be(True)

    result = render(hass, """{{ ['Home Assistant test'] | regex_search('Assist') }}""")
    expect(result).to_be(True)


@test
async def search_test(hass: HomeAssistant = Depends(hass)) -> None:
    """Test search test."""

    result = render(
        hass, r"""{{ '123-456-7890' is search('(\\d{3})-(\\d{3})-(\\d{4})') }}"""
    )
    expect(result).to_be(True)


@test
async def regex_replace(hass: HomeAssistant = Depends(hass)) -> None:
    """Test regex_replace method."""

    result = render(hass, r"""{{ 'Hello World' | regex_replace('(Hello\\s)',) }}""")
    expect(result).to_equal("World")

    result = render(
        hass, """{{ ['Home hinderant test'] | regex_replace('hinder', 'Assist') }}"""
    )
    expect(result).to_equal(["Home Assistant test"])


@test
async def regex_findall(hass: HomeAssistant = Depends(hass)) -> None:
    """Test regex_findall method."""

    result = render(
        hass, """{{ 'Flight from JFK to LHR' | regex_findall('([A-Z]{3})') }}"""
    )
    expect(result).to_equal(["JFK", "LHR"])


@test
async def regex_findall_index(hass: HomeAssistant = Depends(hass)) -> None:
    """Test regex_findall_index method."""

    result = render(
        hass,
        """{{ 'Flight from JFK to LHR' | regex_findall_index('([A-Z]{3})', 0) }}""",
    )
    expect(result).to_equal("JFK")

    result = render(
        hass,
        """{{ 'Flight from JFK to LHR' | regex_findall_index('([A-Z]{3})', 1) }}""",
    )
    expect(result).to_equal("LHR")


@test
async def regex_ignorecase_parameter(hass: HomeAssistant = Depends(hass)) -> None:
    """Test ignorecase parameter across all regex functions."""
    # Test regex_match with ignorecase
    result = render(hass, """{{ 'TEST' | regex_match('test', True) }}""")
    expect(result).to_be(True)

    # Test regex_search with ignorecase
    result = render(hass, """{{ 'TEST STRING' | regex_search('test', True) }}""")
    expect(result).to_be(True)

    # Test regex_replace with ignorecase
    result = render(hass, """{{ 'TEST' | regex_replace('test', 'replaced', True) }}""")
    expect(result).to_equal("replaced")

    # Test regex_findall with ignorecase
    result = render(hass, """{{ 'TEST test Test' | regex_findall('test', True) }}""")
    expect(result).to_equal(["TEST", "test", "Test"])


@test
async def regex_with_non_string_input(hass: HomeAssistant = Depends(hass)) -> None:
    """Test regex functions with non-string input (automatic conversion)."""
    # Test with integer
    result = render(hass, r"""{{ 12345 | regex_match('\\d+') }}""")
    expect(result).to_be(True)

    # Test with list (string conversion)
    result = render(hass, r"""{{ [1, 2, 3] | regex_search('\\d') }}""")
    expect(result).to_be(True)


@test
async def regex_edge_cases(hass: HomeAssistant = Depends(hass)) -> None:
    """Test regex functions with edge cases."""
    # Test with empty string
    expect(render(hass, """{{ '' | regex_match('.*') }}""")).to_be(True)

    # Test regex_findall_index with out of bounds index
    expect(
        lambda: render(hass, """{{ 'test' | regex_findall_index('t', 5) }}""")
    ).to_raise(TemplateError)

    # Test with invalid regex pattern (re.error wrapped in TemplateError)
    expect(lambda: render(hass, """{{ 'test' | regex_match('[') }}""")).to_raise(
        TemplateError
    )


@test
async def regex_groups_and_replacement_patterns(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test regex with groups and replacement patterns."""
    # Test replacement with groups
    result = render(
        hass, r"""{{ 'John Doe' | regex_replace('(\\w+) (\\w+)', '\\2, \\1') }}"""
    )
    expect(result).to_equal("Doe, John")

    # Test findall with groups
    result = render(
        hass,
        r"""{{ 'Email: test@example.com, Phone: 123-456-7890' | regex_findall('(\\w+@\\w+\\.\\w+)|(\\d{3}-\\d{3}-\\d{4})') }}""",
    )
    # The result will contain tuples with empty strings for non-matching groups
    expect(len(result)).to_equal(2)
