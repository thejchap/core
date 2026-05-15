"""Tests for AsusWRT helpers."""

from typing import Any

from tryke import expect, test

from homeassistant.components.asuswrt.helpers import clean_dict, translate_to_legacy

DICT_TO_CLEAN = {
    "key1": "value1",
    "key2": None,
    "key3_state": "value3",
    "key4_state": None,
    "state": None,
}

DICT_CLEAN = {
    "key1": "value1",
    "key3_state": "value3",
    "key4_state": None,
    "state": None,
}

TRANSLATE_0_INPUT = {"usage": "value1", "cpu": "value2"}
TRANSLATE_0_OUTPUT = {"mem_usage_perc": "value1", "CPU": "value2"}

TRANSLATE_1_INPUT = {"wan_rx": "value1", "wan_rrx": "value2"}
TRANSLATE_1_OUTPUT = {"sensor_rx_bytes": "value1", "wan_rrx": "value2"}

TRANSLATE_2_INPUT = ["free", "used"]
TRANSLATE_2_OUTPUT = ["mem_free", "mem_used"]

TRANSLATE_3_INPUT = ["2ghz", "2ghz2"]
TRANSLATE_3_OUTPUT = ["2.4GHz", "2ghz2"]


@test
def clean_dict_strips_none() -> None:
    """Test clean_dict method."""
    expect(clean_dict(DICT_TO_CLEAN)).to_equal(DICT_CLEAN)


@test.cases(
    test.case("none_in_none_out", input=None, expected=None),
    test.case(
        "dict_passthrough",
        input={"key1": "value1", "key2": None},
        expected={"key1": "value1", "key2": None},
    ),
    test.case("dict_translate_0", input=TRANSLATE_0_INPUT, expected=TRANSLATE_0_OUTPUT),
    test.case("dict_translate_1", input=TRANSLATE_1_INPUT, expected=TRANSLATE_1_OUTPUT),
    test.case("empty_dict", input={}, expected={}),
    test.case("list_passthrough", input=["key1", "key2"], expected=["key1", "key2"]),
    test.case("list_translate_2", input=TRANSLATE_2_INPUT, expected=TRANSLATE_2_OUTPUT),
    test.case("list_translate_3", input=TRANSLATE_3_INPUT, expected=TRANSLATE_3_OUTPUT),
    test.case("empty_list", input=[], expected=[]),
    test.case("int_passthrough", input=123, expected=123),
    test.case("string_passthrough", input="string", expected="string"),
    test.case("float_passthrough", input=3.1415926535, expected=3.1415926535),
)
def translate(input: Any, expected: Any) -> None:
    """Test translate method."""
    expect(translate_to_legacy(input)).to_equal(expected)
