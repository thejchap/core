"""Test enum helpers."""

from enum import Enum, IntEnum, IntFlag, StrEnum
from typing import Any

from tryke import expect, test

from homeassistant.util.enum import try_parse_enum


class _AStrEnum(StrEnum):
    VALUE = "value"


class _AnIntEnum(IntEnum):
    VALUE = 1


class _AnIntFlag(IntFlag):
    VALUE = 1
    SECOND = 2


@test.cases(
    test.case(
        "strenum-value",
        enum_type=_AStrEnum,
        value=_AStrEnum.VALUE,
        expected=_AStrEnum.VALUE,
    ),
    test.case(
        "strenum-str", enum_type=_AStrEnum, value="value", expected=_AStrEnum.VALUE
    ),
    test.case(
        "strenum-invalid-str", enum_type=_AStrEnum, value="invalid", expected=None
    ),
    test.case("strenum-invalid-int", enum_type=_AStrEnum, value=1, expected=None),
    test.case("strenum-invalid-none", enum_type=_AStrEnum, value=None, expected=None),
    test.case(
        "intenum-value",
        enum_type=_AnIntEnum,
        value=_AnIntEnum.VALUE,
        expected=_AnIntEnum.VALUE,
    ),
    test.case("intenum-int", enum_type=_AnIntEnum, value=1, expected=_AnIntEnum.VALUE),
    test.case(
        "intenum-invalid-str", enum_type=_AnIntEnum, value="value", expected=None
    ),
    test.case("intenum-invalid-int", enum_type=_AnIntEnum, value=2, expected=None),
    test.case("intenum-invalid-none", enum_type=_AnIntEnum, value=None, expected=None),
    test.case(
        "intflag-value",
        enum_type=_AnIntFlag,
        value=_AnIntFlag.VALUE,
        expected=_AnIntFlag.VALUE,
    ),
    test.case("intflag-int", enum_type=_AnIntFlag, value=1, expected=_AnIntFlag.VALUE),
    test.case("intflag-second", enum_type=_AnIntFlag, value=2, expected=_AnIntFlag(2)),
    test.case(
        "intflag-invalid-str", enum_type=_AnIntFlag, value="value", expected=None
    ),
    test.case("intflag-invalid-none", enum_type=_AnIntFlag, value=None, expected=None),
)
def try_parse(enum_type: type[Enum], value: Any, expected: Enum | None) -> None:
    """Test parsing of values into an Enum."""
    expect(try_parse_enum(enum_type, value) is expected).to_be(True)
