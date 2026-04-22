"""Test functional utility functions for Home Assistant templates."""

from __future__ import annotations

import random
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.helpers import template

from tests.hass_fixtures import hass
from tests.helpers.template.helpers import render


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def apply(hass: HomeAssistant = Depends(hass)) -> None:
    """Test apply."""
    tpl = """
    {%- macro add_foo(arg) -%}
    {{arg}}foo
    {%- endmacro -%}
    {{ ["a", "b", "c"] | map('apply', add_foo) | list }}
    """
    expect(render(hass, tpl)).to_equal(["afoo", "bfoo", "cfoo"])

    expect(
        render(hass, "{{ ['1', '2', '3', '4', '5'] | map('apply', int) | list }}")
    ).to_equal([1, 2, 3, 4, 5])


@test
async def apply_macro_with_arguments(hass: HomeAssistant = Depends(hass)) -> None:
    """Test apply macro with positional, named, and mixed arguments."""
    # Test macro with positional arguments
    tpl = """
                {%- macro add_numbers(a, b, c) -%}
                {{ a + b + c }}
                {%- endmacro -%}
                {{ apply(5, add_numbers, 10, 15) }}
                """
    expect(render(hass, tpl)).to_equal(30)

    # Test macro with named arguments
    tpl = """
                {%- macro greet(name, greeting="Hello") -%}
                {{ greeting }}, {{ name }}!
                {%- endmacro -%}
                {{ apply("World", greet, greeting="Hi") }}
                """
    expect(render(hass, tpl)).to_equal("Hi, World!")

    # Test macro with mixed arguments
    tpl = """
                {%- macro format_message(prefix, name, suffix="!") -%}
                {{ prefix }} {{ name }}{{ suffix }}
                {%- endmacro -%}
                {{ apply("Welcome", format_message, "John", suffix="...") }}
                """
    expect(render(hass, tpl)).to_equal("Welcome John...")


@test
async def as_function(hass: HomeAssistant = Depends(hass)) -> None:
    """Test as_function."""
    tpl = """
        {%- macro macro_double(num, returns) -%}
        {%- do returns(num * 2) -%}
        {%- endmacro -%}
        {%- set double = macro_double | as_function -%}
        {{ double(5) }}
        """
    expect(render(hass, tpl)).to_equal(10)


@test
async def as_function_no_arguments(hass: HomeAssistant = Depends(hass)) -> None:
    """Test as_function with no arguments."""
    tpl = """
        {%- macro macro_get_hello(returns) -%}
        {%- do returns("Hello") -%}
        {%- endmacro -%}
        {%- set get_hello = macro_get_hello | as_function -%}
        {{ get_hello() }}
        """
    expect(render(hass, tpl)).to_equal("Hello")


@test
async def ord_filter(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the ord filter."""
    expect(render(hass, '{{ "d" | ord }}')).to_equal(100)


@test
async def random_every_time(hass: HomeAssistant = Depends(hass)) -> None:
    """Ensure the random filter runs every time, not just once."""
    with patch.object(random, "choice") as test_choice:
        tpl = template.Template("{{ [1,2] | random }}", hass)
        test_choice.return_value = "foo"
        expect(tpl.async_render()).to_equal("foo")
        test_choice.return_value = "bar"
        expect(tpl.async_render()).to_equal("bar")


@test
async def render_with_possible_json_value_valid_with_is_defined(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Render with possible JSON value with known JSON object."""
    tpl = template.Template("{{ value_json.hello|is_defined }}", hass)
    expect(tpl.async_render_with_possible_json_value('{"hello": "world"}')).to_equal(
        "world"
    )


@test
async def render_with_possible_json_value_undefined_json(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Render with possible JSON value with unknown JSON object."""
    tpl = template.Template("{{ value_json.bye|is_defined }}", hass)
    expect(tpl.async_render_with_possible_json_value('{"hello": "world"}')).to_equal(
        '{"hello": "world"}'
    )


@test
async def render_with_possible_json_value_undefined_json_error_value(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Render with possible JSON value with unknown JSON object."""
    tpl = template.Template("{{ value_json.bye|is_defined }}", hass)
    expect(
        tpl.async_render_with_possible_json_value('{"hello": "world"}', "")
    ).to_equal("")


@test
async def iif(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the immediate if function/filter."""

    expect(render(hass, "{{ (1 == 1) | iif }}")).to_be(True)
    expect(render(hass, "{{ (1 == 2) | iif }}")).to_be(False)
    expect(render(hass, "{{ (1 == 1) | iif('yes') }}")).to_equal("yes")
    expect(render(hass, "{{ (1 == 2) | iif('yes') }}")).to_be(False)
    expect(render(hass, "{{ (1 == 2) | iif('yes', 'no') }}")).to_equal("no")
    expect(
        render(hass, "{{ not_exists | default(None) | iif('yes', 'no') }}")
    ).to_equal("no")
    expect(
        render(hass, "{{ not_exists | default(None) | iif('yes', 'no', 'unknown') }}")
    ).to_equal("unknown")
    expect(render(hass, "{{ iif(1 == 1) }}")).to_be(True)
    expect(render(hass, "{{ iif(1 == 2, 'yes', 'no') }}")).to_equal("no")


@test.cases(
    test.case("zero_in_zero", seq=[0], value=0, expected=True),
    test.case("one_not_zero", seq=[1], value=0, expected=False),
    test.case("false_in_zero", seq=[False], value=0, expected=True),
    test.case("true_not_zero", seq=[True], value=0, expected=False),
    test.case("zero_not_list_zero", seq=[0], value=[0], expected=False),
    test.case("toto_in_mixed", seq=["toto", 1], value="toto", expected=True),
    test.case("tata_not_in_mixed", seq=["toto", 1], value="tata", expected=False),
    test.case("empty_list", seq=[], value=0, expected=False),
    test.case("empty_list_none", seq=[], value=None, expected=False),
)
async def contains(
    seq: list,
    value: object,
    expected: bool,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test contains."""
    expect(
        render(hass, "{{ seq | contains(value) }}", {"seq": seq, "value": value})
    ).to_equal(expected)
    expect(
        render(hass, "{{ seq is contains(value) }}", {"seq": seq, "value": value})
    ).to_equal(expected)


@test
async def merge_response_with_entity_id_in_response(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the merge_response function/filter with empty lists."""

    service_response = {
        "test.response": {"some_key": True, "entity_id": "test.response"},
        "test.response2": {"some_key": False, "entity_id": "test.response2"},
    }
    _template = "{{ merge_response(" + str(service_response) + ") }}"
    expect(lambda: render(hass, _template)).to_raise(
        TemplateError,
        match="ValueError: Response dictionary already contains key 'entity_id'",
    )

    service_response = {
        "test.response": {
            "happening": [
                {
                    "start": "2024-02-27T17:00:00-06:00",
                    "end": "2024-02-27T18:00:00-06:00",
                    "summary": "Magic day",
                    "entity_id": "test.response",
                }
            ]
        }
    }
    _template = "{{ merge_response(" + str(service_response) + ") }}"
    expect(lambda: render(hass, _template)).to_raise(
        TemplateError,
        match="ValueError: Response dictionary already contains key 'entity_id'",
    )


@test
async def response_empty_dict(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the merge_response function/filter with empty dict."""

    service_response: dict = {}
    _template = "{{ merge_response(" + str(service_response) + ") }}"

    result = render(hass, _template)
    expect(result).to_equal([])


@test
async def response_incorrect_value(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the merge_response function/filter with incorrect response."""

    service_response = "incorrect"
    _template = "{{ merge_response(" + str(service_response) + ") }}"
    expect(lambda: render(hass, _template)).to_raise(
        TemplateError, match="TypeError: Response is not a dictionary"
    )


@test
async def merge_response_with_incorrect_response(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the merge_response function/filter with empty response should raise."""

    service_response: dict = {"calendar.sports": []}
    _template = "{{ merge_response(" + str(service_response) + ") }}"
    expect(lambda: render(hass, _template)).to_raise(
        TemplateError, match="TypeError: Response is not a dictionary"
    )

    service_response = {
        "binary_sensor.workday": [],
    }
    _template = "{{ merge_response(" + str(service_response) + ") }}"
    expect(lambda: render(hass, _template)).to_raise(
        TemplateError, match="TypeError: Response is not a dictionary"
    )


@test
async def merge_response_not_mutate_original_object(
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test the merge_response does not mutate original service response value."""

    value = '{"calendar.family": {"events": [{"summary": "An event"}]}'
    _template = (
        "{% set calendar_response = " + value + "} %}"
        "{{ merge_response(calendar_response) }}"
        # We should be able to merge the same response again
        # as the merge is working on a copy of the original object (response)
        "{{ merge_response(calendar_response) }}"
    )

    expect(bool(render(hass, _template))).to_be(True)


@test
async def typeof(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the typeof debug filter/function."""
    expect(render(hass, "{{ True | typeof }}")).to_equal("bool")
    expect(render(hass, "{{ typeof(True) }}")).to_equal("bool")

    expect(render(hass, "{{ [1, 2, 3] | typeof }}")).to_equal("list")
    expect(render(hass, "{{ typeof([1, 2, 3]) }}")).to_equal("list")

    expect(render(hass, "{{ 1 | typeof }}")).to_equal("int")
    expect(render(hass, "{{ typeof(1) }}")).to_equal("int")

    expect(render(hass, "{{ 1.1 | typeof }}")).to_equal("float")
    expect(render(hass, "{{ typeof(1.1) }}")).to_equal("float")

    expect(render(hass, "{{ None | typeof }}")).to_equal("NoneType")
    expect(render(hass, "{{ typeof(None) }}")).to_equal("NoneType")

    expect(render(hass, "{{ 'Home Assistant' | typeof }}")).to_equal("str")
    expect(render(hass, "{{ typeof('Home Assistant') }}")).to_equal("str")


@test
async def combine(hass: HomeAssistant = Depends(hass)) -> None:
    """Test combine filter and function."""
    expect(
        render(hass, "{{ {'a': 1, 'b': 2} | combine({'b': 3, 'c': 4}) }}")
    ).to_equal({"a": 1, "b": 3, "c": 4})

    expect(
        render(hass, "{{ combine({'a': 1, 'b': 2}, {'b': 3, 'c': 4}) }}")
    ).to_equal({"a": 1, "b": 3, "c": 4})

    expect(
        render(
            hass,
            "{{ combine({'a': 1, 'b': {'x': 1}}, {'b': {'y': 2}, 'c': 4}, recursive=True) }}",
        )
    ).to_equal({"a": 1, "b": {"x": 1, "y": 2}, "c": 4})

    # Test that recursive=False does not merge nested dictionaries
    expect(
        render(
            hass,
            "{{ combine({'a': 1, 'b': {'x': 1}}, {'b': {'y': 2}, 'c': 4}, recursive=False) }}",
        )
    ).to_equal({"a": 1, "b": {"y": 2}, "c": 4})

    # Test that None values are handled correctly in recursive merge
    expect(
        render(
            hass,
            "{{ combine({'a': 1, 'b': none}, {'b': {'y': 2}, 'c': 4}, recursive=True) }}",
        )
    ).to_equal({"a": 1, "b": {"y": 2}, "c": 4})

    expect(lambda: render(hass, "{{ combine() }}")).to_raise(
        TemplateError, match="combine expected at least 1 argument, got 0"
    )

    expect(lambda: render(hass, "{{ {'a': 1} | combine('not a dict') }}")).to_raise(
        TemplateError, match="combine expected a dict, got str"
    )
