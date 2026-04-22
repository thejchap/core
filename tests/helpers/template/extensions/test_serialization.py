"""Test serialization functions for Home Assistant templates."""

from __future__ import annotations

import json
from typing import Any

from tryke import Depends, expect, fixture, test
import orjson

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError

from tests.hass_fixtures import caplog, hass
from tests.helpers.template.helpers import render, render_to_info


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def to_json(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the object to JSON string filter."""

    # Note that we're not testing the actual json.loads and json.dumps methods,
    # only the filters, so we don't need to be exhaustive with our sample JSON.
    expected_result: Any = {"Foo": "Bar"}
    actual_result: Any = render(hass, "{{ {'Foo': 'Bar'} | to_json }}")
    expect(actual_result).to_equal(expected_result)

    expected_result = orjson.dumps({"Foo": "Bar"}, option=orjson.OPT_INDENT_2).decode()
    actual_result = render(
        hass, "{{ {'Foo': 'Bar'} | to_json(pretty_print=True) }}", parse_result=False
    )
    expect(actual_result).to_equal(expected_result)

    expected_result = orjson.dumps(
        {"Z": 26, "A": 1, "M": 13}, option=orjson.OPT_SORT_KEYS
    ).decode()
    actual_result = render(
        hass,
        "{{ {'Z': 26, 'A': 1, 'M': 13} | to_json(sort_keys=True) }}",
        parse_result=False,
    )
    expect(actual_result).to_equal(expected_result)

    expect(lambda: render(hass, "{{ {'Foo': now()} | to_json }}")).to_raise(
        TemplateError
    )

    # Test special case where substring class cannot be rendered
    # See: https://github.com/ijl/orjson/issues/445
    class MyStr(str):
        __slots__ = ()

    expected_result = '{"mykey1":11.0,"mykey2":"myvalue2","mykey3":["opt3b","opt3a"]}'
    test_dict = {
        MyStr("mykey2"): "myvalue2",
        MyStr("mykey1"): 11.0,
        MyStr("mykey3"): ["opt3b", "opt3a"],
    }
    actual_result = render(
        hass,
        "{{ test_dict | to_json(sort_keys=True) }}",
        {"test_dict": test_dict},
        parse_result=False,
    )
    expect(actual_result).to_equal(expected_result)


@test
async def to_json_ensure_ascii(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the object to JSON string filter."""

    # Note that we're not testing the actual json.loads and json.dumps methods,
    # only the filters, so we don't need to be exhaustive with our sample JSON.
    actual_value_ascii = render(hass, "{{ 'Bar ҝ éèà' | to_json(ensure_ascii=True) }}")
    expect(actual_value_ascii).to_equal('"Bar \\u049d \\u00e9\\u00e8\\u00e0"')
    actual_value = render(hass, "{{ 'Bar ҝ éèà' | to_json(ensure_ascii=False) }}")
    expect(actual_value).to_equal('"Bar ҝ éèà"')

    expected_result = json.dumps({"Foo": "Bar"}, indent=2)
    actual_result = render(
        hass,
        "{{ {'Foo': 'Bar'} | to_json(pretty_print=True, ensure_ascii=True) }}",
        parse_result=False,
    )
    expect(actual_result).to_equal(expected_result)

    expected_result = json.dumps({"Z": 26, "A": 1, "M": 13}, sort_keys=True)
    actual_result = render(
        hass,
        "{{ {'Z': 26, 'A': 1, 'M': 13} | to_json(sort_keys=True, ensure_ascii=True) }}",
        parse_result=False,
    )
    expect(actual_result).to_equal(expected_result)


@test
async def from_json(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the JSON string to object filter."""

    # Note that we're not testing the actual json.loads and json.dumps methods,
    # only the filters, so we don't need to be exhaustive with our sample JSON.
    expected_result = "Bar"
    actual_result = render(hass, '{{ (\'{"Foo": "Bar"}\' | from_json).Foo }}')
    expect(actual_result).to_equal(expected_result)

    info = render_to_info(hass, "{{ 'garbage string' | from_json }}")
    expect(lambda: info.result()).to_raise(TemplateError, match="no default was specified")

    actual_result = render(hass, "{{ 'garbage string' | from_json('Bar') }}")
    expect(actual_result).to_equal(expected_result)


@test
async def from_hex(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the fromhex filter."""
    expect(render(hass, "{{ '0F010003' | from_hex }}")).to_equal(b"\x0f\x01\x00\x03")


@test
async def pack(
    hass: HomeAssistant = Depends(hass),
    caplog: Any = Depends(caplog),
) -> None:
    """Test struct pack method."""

    # render as filter
    variables = {"value": 0xDEADBEEF}
    expect(render(hass, "{{ value | pack('>I') }}", variables)).to_equal(
        b"\xde\xad\xbe\xef"
    )

    # render as function
    expect(render(hass, "{{ pack(value, '>I') }}", variables)).to_equal(
        b"\xde\xad\xbe\xef"
    )

    # test with None value
    expect(render(hass, "{{ pack(value, '>I') }}", {"value": None})).to_be(None)
    expect(
        "Template warning: 'pack' unable to pack object 'None' with type 'NoneType' and"
        " format_string '>I' see https://docs.python.org/3/library/struct.html for more"
        " information" in caplog.text
    ).to_be(True)

    # test with invalid filter
    expect(
        render(hass, "{{ pack(value, 'invalid filter') }}", variables)
    ).to_be(None)
    expect(
        "Template warning: 'pack' unable to pack object '3735928559' with type 'int'"
        " and format_string 'invalid filter' see"
        " https://docs.python.org/3/library/struct.html for more information"
        in caplog.text
    ).to_be(True)


@test
async def unpack(
    hass: HomeAssistant = Depends(hass),
    caplog: Any = Depends(caplog),
) -> None:
    """Test struct unpack method."""

    variables = {"value": b"\xde\xad\xbe\xef"}

    # render as filter
    result = render(hass, """{{ value | unpack('>I') }}""", variables)
    expect(result).to_equal(0xDEADBEEF)

    # render as function
    result = render(hass, """{{ unpack(value, '>I') }}""", variables)
    expect(result).to_equal(0xDEADBEEF)

    # unpack with offset
    result = render(hass, """{{ unpack(value, '>H', offset=2) }}""", variables)
    expect(result).to_equal(0xBEEF)

    # test with an empty bytes object
    expect(render(hass, """{{ unpack(value, '>I') }}""", {"value": b""})).to_be(None)
    expect(
        "Template warning: 'unpack' unable to unpack object 'b''' with format_string"
        " '>I' and offset 0 see https://docs.python.org/3/library/struct.html for more"
        " information" in caplog.text
    ).to_be(True)

    # test with invalid filter
    expect(
        render(hass, """{{ unpack(value, 'invalid filter') }}""", {"value": b""})
    ).to_be(None)
    expect(
        "Template warning: 'unpack' unable to unpack object 'b''' with format_string"
        " 'invalid filter' and offset 0 see"
        " https://docs.python.org/3/library/struct.html for more information"
        in caplog.text
    ).to_be(True)
