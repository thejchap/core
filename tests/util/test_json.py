"""Test Home Assistant json utility functions."""

from pathlib import Path
import re

import orjson
from tryke import Depends, expect, fixture, test

from homeassistant.exceptions import HomeAssistantError
from homeassistant.util.json import (
    json_loads,
    json_loads_array as _json_loads_array,
    json_loads_object as _json_loads_object,
    load_json,
    load_json_array,
    load_json_object,
)

from tests.hass_fixtures import tmp_path

# Test data that can be saved as JSON
TEST_JSON_A = {"a": 1, "B": "two"}
# Test data that cannot be loaded as JSON
TEST_BAD_SERIALIED = "THIS IS NOT JSON\n"


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture so imported fixtures resolve via Depends()."""
    return 0


@test
def load_bad_data(tmp_path: Path = Depends(tmp_path)) -> None:
    """Test error from trying to load unserializable data."""
    fname = tmp_path / "test5.json"
    with open(fname, "w", encoding="utf8") as fh:
        fh.write(TEST_BAD_SERIALIED)
    raised: HomeAssistantError | None = None
    try:
        load_json(fname)
    except HomeAssistantError as exc:
        raised = exc
    expect(raised).not_.to_be(None)
    assert raised is not None
    expect(bool(re.search(re.escape(str(fname)), str(raised)))).to_be(True)
    expect(isinstance(raised.__cause__, ValueError)).to_be(True)


@test
def load_json_os_error() -> None:
    """Test trying to load JSON data from a directory."""
    fname = "/"
    raised: HomeAssistantError | None = None
    try:
        load_json(fname)
    except HomeAssistantError as exc:
        raised = exc
    expect(raised).not_.to_be(None)
    assert raised is not None
    expect(bool(re.search(re.escape(str(fname)), str(raised)))).to_be(True)
    expect(isinstance(raised.__cause__, OSError)).to_be(True)


@test
def load_json_file_not_found_error() -> None:
    """Test trying to load object data from inexistent JSON file."""
    fname = "invalid_file.json"

    expect(load_json(fname)).to_equal({})
    expect(load_json(fname, default="")).to_equal("")
    expect(load_json_object(fname)).to_equal({})
    expect(load_json_object(fname, default={"Hi": "Peter"})).to_equal({"Hi": "Peter"})
    expect(load_json_array(fname)).to_equal([])
    expect(load_json_array(fname, default=["Hi"])).to_equal(["Hi"])


@test
def load_json_value_data(tmp_path: Path = Depends(tmp_path)) -> None:
    """Test trying to load object data from JSON file."""
    fname = tmp_path / "test5.json"
    with open(fname, "w", encoding="utf8") as handle:
        handle.write('"two"')

    expect(load_json(fname)).to_equal("two")
    expect(lambda: load_json_object(fname)).to_raise(
        HomeAssistantError, match="Expected JSON to be parsed as a dict"
    )
    expect(lambda: load_json_array(fname)).to_raise(
        HomeAssistantError, match="Expected JSON to be parsed as a list"
    )


@test
def load_json_object_data(tmp_path: Path = Depends(tmp_path)) -> None:
    """Test trying to load object data from JSON file."""
    fname = tmp_path / "test5.json"
    with open(fname, "w", encoding="utf8") as handle:
        handle.write('{"a": 1, "B": "two"}')

    expect(load_json(fname)).to_equal({"a": 1, "B": "two"})
    expect(load_json_object(fname)).to_equal({"a": 1, "B": "two"})
    expect(lambda: load_json_array(fname)).to_raise(
        HomeAssistantError, match="Expected JSON to be parsed as a list"
    )


@test
def load_json_array_data(tmp_path: Path = Depends(tmp_path)) -> None:
    """Test trying to load array data from JSON file."""
    fname = tmp_path / "test5.json"
    with open(fname, "w", encoding="utf8") as handle:
        handle.write('[{"a": 1, "B": "two"}]')

    expect(load_json(fname)).to_equal([{"a": 1, "B": "two"}])
    expect(load_json_array(fname)).to_equal([{"a": 1, "B": "two"}])
    expect(lambda: load_json_object(fname)).to_raise(
        HomeAssistantError, match="Expected JSON to be parsed as a dict"
    )


@test
def json_loads_array() -> None:
    """Test json_loads_array validates result."""
    expect(_json_loads_array('[{"c":1.2}]')).to_equal([{"c": 1.2}])
    expect(lambda: _json_loads_array("{}")).to_raise(
        ValueError, match="Expected JSON to be parsed as a list got <class 'dict'>"
    )
    expect(lambda: _json_loads_array("true")).to_raise(
        ValueError, match="Expected JSON to be parsed as a list got <class 'bool'>"
    )
    expect(lambda: _json_loads_array("null")).to_raise(
        ValueError, match="Expected JSON to be parsed as a list got <class 'NoneType'>"
    )


@test
def json_loads_object() -> None:
    """Test json_loads_object validates result."""
    expect(_json_loads_object('{"c":1.2}')).to_equal({"c": 1.2})
    expect(lambda: _json_loads_object("[]")).to_raise(
        ValueError, match="Expected JSON to be parsed as a dict got <class 'list'>"
    )
    expect(lambda: _json_loads_object("true")).to_raise(
        ValueError, match="Expected JSON to be parsed as a dict got <class 'bool'>"
    )
    expect(lambda: _json_loads_object("null")).to_raise(
        ValueError, match="Expected JSON to be parsed as a dict got <class 'NoneType'>"
    )


@test
async def loading_derived_class() -> None:
    """Test loading data from classes derived from str."""

    class MyStr(str):
        __slots__ = ()

    class MyBytes(bytes):
        pass

    expect(json_loads('"abc"')).to_equal("abc")
    expect(json_loads(MyStr('"abc"'))).to_equal("abc")

    expect(json_loads(b'"abc"')).to_equal("abc")
    expect(lambda: json_loads(MyBytes(b'"abc"'))).to_raise(orjson.JSONDecodeError)
