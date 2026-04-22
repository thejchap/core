"""Test datetime template functions."""

from __future__ import annotations

from datetime import datetime
from types import MappingProxyType
from typing import Any
from unittest.mock import patch

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.exceptions import TemplateError
from homeassistant.util import dt as dt_util
from homeassistant.util.read_only_dict import ReadOnlyDict

from tests.hass_fixtures import hass
from tests.helpers.template.helpers import render, render_to_info


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test.cases(
    test.case("list", [1, 2], False),
    test.case("set", {1, 2}, False),
    test.case("dict", {"a": 1, "b": 2}, False),
    test.case("read_only_dict", ReadOnlyDict({"a": 1, "b": 2}), False),
    test.case("mapping_proxy", MappingProxyType({"a": 1, "b": 2}), False),
    test.case("str", "abc", False),
    test.case("bytes", b"abc", False),
    test.case("tuple", (1, 2), False),
    test.case("datetime", datetime(2024, 1, 1, 0, 0, 0), True),
)
async def is_datetime(
    value: Any,
    expected: bool,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test is datetime."""
    expect(render(hass, "{{ value is datetime }}", {"value": value})).to_equal(expected)


@test
async def strptime(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the parse timestamp method."""
    tests: list[tuple[str, str, str | None]] = [
        ("2016-10-19 15:22:05.588122 UTC", "%Y-%m-%d %H:%M:%S.%f %Z", None),
        ("2016-10-19 15:22:05.588122+0100", "%Y-%m-%d %H:%M:%S.%f%z", None),
        ("2016-10-19 15:22:05.588122", "%Y-%m-%d %H:%M:%S.%f", None),
        ("2016-10-19", "%Y-%m-%d", None),
        ("2016", "%Y", None),
        ("15:22:05", "%H:%M:%S", None),
    ]

    for inp, fmt, expected in tests:
        exp = expected if expected is not None else str(datetime.strptime(inp, fmt))
        temp = f"{{{{ strptime('{inp}', '{fmt}') }}}}"
        expect(render(hass, temp)).to_equal(exp)

    # Test handling of invalid input
    invalid_tests = [
        ("1469119144", "%Y"),
        ("invalid", "%Y"),
    ]

    for inp, fmt in invalid_tests:
        temp = f"{{{{ strptime('{inp}', '{fmt}') }}}}"
        expect(lambda t=temp: render(hass, t)).to_raise(TemplateError)

    # Test handling of default return value
    expect(render(hass, "{{ strptime('invalid', '%Y', 1) }}")).to_equal(1)
    expect(render(hass, "{{ strptime('invalid', '%Y', default=1) }}")).to_equal(1)


@test
async def timestamp_custom(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the timestamps to custom filter."""
    await hass.config.async_set_time_zone("UTC")
    now = dt_util.utcnow()
    tests = [
        (1469119144, None, True, "2016-07-21 16:39:04"),
        (1469119144, "%Y", True, 2016),
        (1469119144, "invalid", True, "invalid"),
        (dt_util.as_timestamp(now), None, False, now.strftime("%Y-%m-%d %H:%M:%S")),
    ]

    for inp, fmt, local, out in tests:
        if fmt:
            fil = f"timestamp_custom('{fmt}')"
        elif fmt and local:
            fil = f"timestamp_custom('{fmt}', {local})"
        else:
            fil = "timestamp_custom"

        expect(render(hass, f"{{{{ {inp} | {fil} }}}}")).to_equal(out)

    # Test handling of invalid input
    invalid_tests = [
        (None, None, None),
    ]

    for inp, fmt, local in invalid_tests:
        if fmt:
            fil = f"timestamp_custom('{fmt}')"
        elif fmt and local:
            fil = f"timestamp_custom('{fmt}', {local})"
        else:
            fil = "timestamp_custom"

        expect(lambda f=fil, i=inp: render(hass, f"{{{{ {i} | {f} }}}}")).to_raise(
            TemplateError
        )

    # Test handling of default return value
    expect(render(hass, "{{ None | timestamp_custom('invalid', True, 1) }}")).to_equal(
        1
    )
    expect(render(hass, "{{ None | timestamp_custom(default=1) }}")).to_equal(1)


@test
async def timestamp_local(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the timestamps to local filter."""
    await hass.config.async_set_time_zone("UTC")
    tests = [
        (1469119144, "2016-07-21T16:39:04+00:00"),
    ]

    for inp, out in tests:
        expect(render(hass, f"{{{{ {inp} | timestamp_local }}}}")).to_equal(out)

    # Test handling of invalid input
    invalid_tests = [
        None,
    ]

    for inp in invalid_tests:
        expect(
            lambda i=inp: render(hass, f"{{{{ {i} | timestamp_local }}}}")
        ).to_raise(TemplateError)

    # Test handling of default return value
    expect(render(hass, "{{ None | timestamp_local(1) }}")).to_equal(1)
    expect(render(hass, "{{ None | timestamp_local(default=1) }}")).to_equal(1)


@test.cases(
    test.case("utc_offset", "2021-06-03 13:00:00.000000+00:00"),
    test.case("iso_z", "1986-07-09T12:00:00Z"),
    test.case("tz_offset", "2016-10-19 15:22:05.588122+0100"),
    test.case("date_only", "2016-10-19"),
    test.case("naive", "2021-01-01 00:00:01"),
    test.case("invalid", "invalid"),
)
async def as_datetime(
    input_value: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test converting a timestamp string to a date object."""
    parsed = dt_util.parse_datetime(input_value)
    expected = str(parsed) if parsed is not None else None
    expect(render(hass, f"{{{{ as_datetime('{input_value}') }}}}")).to_equal(expected)
    expect(render(hass, f"{{{{ '{input_value}' | as_datetime }}}}")).to_equal(expected)


@test.cases(
    test.case("int", 1469119144, "2016-07-21 16:39:04+00:00"),
    test.case("float", 1469119144.0, "2016-07-21 16:39:04+00:00"),
    test.case("negative", -1, "1969-12-31 23:59:59+00:00"),
)
async def as_datetime_from_timestamp(
    input_value: float,
    output: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test converting a UNIX timestamp to a date object."""
    expect(render(hass, f"{{{{ as_datetime({input_value}) }}}}")).to_equal(output)
    expect(render(hass, f"{{{{ {input_value} | as_datetime }}}}")).to_equal(output)
    expect(render(hass, f"{{{{ as_datetime('{input_value}') }}}}")).to_equal(output)
    expect(render(hass, f"{{{{ '{input_value}' | as_datetime }}}}")).to_equal(output)


@test.cases(
    test.case(
        "datetime_with_tz",
        "{% set dt = as_datetime('2024-01-01 16:00:00-08:00') %}",
        "2024-01-01 16:00:00-08:00",
    ),
    test.case(
        "date_only",
        "{% set dt = as_datetime('2024-01-29').date() %}",
        "2024-01-29 00:00:00",
    ),
)
async def as_datetime_from_datetime(
    input_value: str,
    output: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test using datetime.datetime or datetime.date objects as input."""
    expect(render(hass, f"{input_value}{{{{ dt | as_datetime }}}}")).to_equal(output)
    expect(render(hass, f"{input_value}{{{{ as_datetime(dt) }}}}")).to_equal(output)


@test.cases(
    test.case("int_ignored", 1469119144, 123, "2016-07-21 16:39:04+00:00"),
    test.case("str_default_list", '"invalid"', ["default output"], ["default output"]),
    test.case("list_default_zero", ["a", "list"], 0, 0),
    test.case("dict_default_none", {"a": "dict"}, None, None),
)
async def as_datetime_default(
    input_value: Any,
    default: Any,
    output: Any,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test invalid input and return default value."""
    expect(
        render(hass, f"{{{{ as_datetime({input_value}, default={default}) }}}}")
    ).to_equal(output)
    expect(render(hass, f"{{{{ {input_value} | as_datetime({default}) }}}}")).to_equal(
        output
    )


@test
async def as_local(hass: HomeAssistant = Depends(hass)) -> None:
    """Test converting time to local."""

    hass.states.async_set("test.object", "available")
    last_updated = hass.states.get("test.object").last_updated
    expect(render(hass, "{{ as_local(states.test.object.last_updated) }}")).to_equal(
        str(dt_util.as_local(last_updated))
    )
    expect(render(hass, "{{ states.test.object.last_updated | as_local }}")).to_equal(
        str(dt_util.as_local(last_updated))
    )


@test
async def timestamp_utc(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the timestamps to local filter."""
    now = dt_util.utcnow()
    tests = [
        (1469119144, "2016-07-21T16:39:04+00:00"),
        (dt_util.as_timestamp(now), now.isoformat()),
    ]

    for inp, out in tests:
        expect(render(hass, f"{{{{ {inp} | timestamp_utc }}}}")).to_equal(out)

    # Test handling of invalid input
    invalid_tests = [
        None,
    ]

    for inp in invalid_tests:
        expect(
            lambda i=inp: render(hass, f"{{{{ {i} | timestamp_utc }}}}")
        ).to_raise(TemplateError)

    # Test handling of default return value
    expect(render(hass, "{{ None | timestamp_utc(1) }}")).to_equal(1)
    expect(render(hass, "{{ None | timestamp_utc(default=1) }}")).to_equal(1)


@test
async def as_timestamp(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the as_timestamp function."""
    expect(lambda: render(hass, '{{ as_timestamp("invalid") }}')).to_raise(
        TemplateError
    )

    hass.states.async_set("test.object", None)
    expect(lambda: render(hass, "{{ as_timestamp(states.test.object) }}")).to_raise(
        TemplateError
    )

    tpl = (
        '{{ as_timestamp(strptime("2024-02-03T09:10:24+0000", '
        '"%Y-%m-%dT%H:%M:%S%z")) }}'
    )
    expect(render(hass, tpl)).to_equal(1706951424.0)

    # Test handling of default return value
    expect(render(hass, "{{ 'invalid' | as_timestamp(1) }}")).to_equal(1)
    expect(render(hass, "{{ 'invalid' | as_timestamp(default=1) }}")).to_equal(1)
    expect(render(hass, "{{ as_timestamp('invalid', 1) }}")).to_equal(1)
    expect(render(hass, "{{ as_timestamp('invalid', default=1) }}")).to_equal(1)


@test
async def as_timedelta(hass: HomeAssistant = Depends(hass)) -> None:
    """Test the as_timedelta function/filter."""

    result = render(hass, "{{ as_timedelta('PT10M') }}")
    expect(result).to_equal("0:10:00")

    result = render(hass, "{{ 'PT10M' | as_timedelta }}")
    expect(result).to_equal("0:10:00")

    result = render(hass, "{{ 'T10M' | as_timedelta }}")
    expect(result).to_be(None)


@test
async def now_function(hass: HomeAssistant = Depends(hass)) -> None:
    """Test now method."""
    with patch(
        "homeassistant.helpers.template.TemplateEnvironment.is_safe_callable",
        return_value=True,
    ):
        now = dt_util.now()
        with freeze_time(now):
            info = render_to_info(hass, "{{ now().isoformat() }}")
            expect(info.result()).to_equal(now.isoformat())

        expect(info.has_time).to_be(True)


@test
async def utcnow_function(hass: HomeAssistant = Depends(hass)) -> None:
    """Test now method."""
    with patch(
        "homeassistant.helpers.template.TemplateEnvironment.is_safe_callable",
        return_value=True,
    ):
        utcnow = dt_util.utcnow()
        with freeze_time(utcnow):
            info = render_to_info(hass, "{{ utcnow().isoformat() }}")
            expect(info.result()).to_equal(utcnow.isoformat())

        expect(info.has_time).to_be(True)


@test.cases(
    test.case(
        "host_clock_utc",
        "2021-11-24 03:00:00+00:00",
        "2021-11-23T10:00:00-08:00",
        "2021-11-23T00:00:00-08:00",
        "America/Los_Angeles",
    ),
    test.case(
        "host_clock_local",
        "2021-11-23 19:00:00-08:00",
        "2021-11-23T10:00:00-08:00",
        "2021-11-23T00:00:00-08:00",
        "America/Los_Angeles",
    ),
)
async def today_at_function(
    now: str,
    expected: str,
    expected_midnight: str,
    timezone_str: str,
    hass: HomeAssistant = Depends(hass),
) -> None:
    """Test today_at method."""
    with patch(
        "homeassistant.helpers.template.TemplateEnvironment.is_safe_callable",
        return_value=True,
    ):
        freezer = freeze_time(now)
        freezer.start()
        try:
            await hass.config.async_set_time_zone(timezone_str)

            result = render(hass, "{{ today_at('10:00').isoformat() }}")
            expect(result).to_equal(expected)

            result = render(hass, "{{ today_at('10:00:00').isoformat() }}")
            expect(result).to_equal(expected)

            result = render(hass, "{{ ('10:00:00' | today_at).isoformat() }}")
            expect(result).to_equal(expected)

            result = render(hass, "{{ today_at().isoformat() }}")
            expect(result).to_equal(expected_midnight)

            expect(lambda: render(hass, "{{ today_at('bad') }}")).to_raise(
                TemplateError
            )

            info = render_to_info(hass, "{{ today_at('10:00').isoformat() }}")
            expect(info.has_time).to_be(True)
        finally:
            freezer.stop()


@test
async def relative_time(hass: HomeAssistant = Depends(hass)) -> None:
    """Test relative_time method."""
    with patch(
        "homeassistant.helpers.template.TemplateEnvironment.is_safe_callable",
        return_value=True,
    ):
        await hass.config.async_set_time_zone("UTC")
        now = datetime.strptime("2000-01-01 10:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
        relative_time_template = (
            '{{relative_time(strptime("2000-01-01 09:00:00", "%Y-%m-%d %H:%M:%S"))}}'
        )
        with freeze_time(now):
            result = render(hass, relative_time_template)
            expect(result).to_equal("1 hour")
            result = render(
                hass,
                (
                    "{{"
                    "  relative_time("
                    "    strptime("
                    '        "2000-01-01 09:00:00 +01:00",'
                    '        "%Y-%m-%d %H:%M:%S %z"'
                    "    )"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("2 hours")

            result = render(
                hass,
                (
                    "{{"
                    "  relative_time("
                    "    strptime("
                    '       "2000-01-01 03:00:00 -06:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"'
                    "    )"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("1 hour")

            result1 = str(
                datetime.strptime(
                    "2000-01-01 11:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z"
                )
            )
            result2 = render(
                hass,
                (
                    "{{"
                    "  relative_time("
                    "    strptime("
                    '       "2000-01-01 11:00:00 +00:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"'
                    "    )"
                    "  )"
                    "}}"
                ),
            )
            expect(result2).to_equal(result1)

            result = render(hass, '{{relative_time("string")}}')
            expect(result).to_equal("string")

            # Test behavior when current time is same as the input time
            result = render(
                hass,
                (
                    "{{"
                    "  relative_time("
                    "    strptime("
                    '        "2000-01-01 10:00:00 +00:00",'
                    '        "%Y-%m-%d %H:%M:%S %z"'
                    "    )"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("0 seconds")

            # Test behavior when the input time is in the future
            result = render(
                hass,
                (
                    "{{"
                    "  relative_time("
                    "    strptime("
                    '        "2000-01-01 11:00:00 +00:00",'
                    '        "%Y-%m-%d %H:%M:%S %z"'
                    "    )"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("2000-01-01 11:00:00+00:00")

            info = render_to_info(hass, relative_time_template)
            expect(info.has_time).to_be(True)


@test
async def time_since(hass: HomeAssistant = Depends(hass)) -> None:
    """Test time_since method."""
    with patch(
        "homeassistant.helpers.template.TemplateEnvironment.is_safe_callable",
        return_value=True,
    ):
        await hass.config.async_set_time_zone("UTC")
        now = datetime.strptime("2000-01-01 10:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
        time_since_template = (
            '{{time_since(strptime("2000-01-01 09:00:00", "%Y-%m-%d %H:%M:%S"))}}'
        )
        with freeze_time(now):
            result = render(hass, time_since_template)
            expect(result).to_equal("1 hour")

            result = render(
                hass,
                (
                    "{{"
                    "  time_since("
                    "    strptime("
                    '        "2000-01-01 09:00:00 +01:00",'
                    '        "%Y-%m-%d %H:%M:%S %z"'
                    "    )"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("2 hours")

            result = render(
                hass,
                (
                    "{{"
                    "  time_since("
                    "    strptime("
                    '       "2000-01-01 03:00:00 -06:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"'
                    "    )"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("1 hour")

            result1 = str(
                datetime.strptime(
                    "2000-01-01 11:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z"
                )
            )
            result2 = render(
                hass,
                (
                    "{{"
                    "  time_since("
                    "    strptime("
                    '       "2000-01-01 11:00:00 +00:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"),'
                    "    precision = 2"
                    "  )"
                    "}}"
                ),
            )
            expect(result2).to_equal(result1)

            result = render(
                hass,
                (
                    "{{"
                    "  time_since("
                    "    strptime("
                    '        "2000-01-01 09:05:00 +01:00",'
                    '        "%Y-%m-%d %H:%M:%S %z"),'
                    "       precision=2"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("1 hour 55 minutes")

            result = render(
                hass,
                (
                    "{{"
                    "  time_since("
                    "    strptime("
                    '       "2000-01-01 02:05:27 -06:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"),'
                    "       precision = 3"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("1 hour 54 minutes 33 seconds")
            result = render(
                hass,
                (
                    "{{"
                    "  time_since("
                    "    strptime("
                    '       "2000-01-01 02:05:27 -06:00",'
                    '       "%Y-%m-%d %H:%M:%S %z")'
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("2 hours")
            result = render(
                hass,
                (
                    "{{"
                    "  time_since("
                    "    strptime("
                    '       "1999-02-01 02:05:27 -06:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"),'
                    "       precision = 0"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("11 months 4 days 1 hour 54 minutes 33 seconds")
            result = render(
                hass,
                (
                    "{{"
                    "  time_since("
                    "    strptime("
                    '       "1999-02-01 02:05:27 -06:00",'
                    '       "%Y-%m-%d %H:%M:%S %z")'
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("11 months")
            result1 = str(
                datetime.strptime(
                    "2000-01-01 11:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z"
                )
            )
            result2 = render(
                hass,
                (
                    "{{"
                    "  time_since("
                    "    strptime("
                    '       "2000-01-01 11:00:00 +00:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"),'
                    "       precision=3"
                    "  )"
                    "}}"
                ),
            )
            expect(result2).to_equal(result1)

            result = render(hass, '{{time_since("string")}}')
            expect(result).to_equal("string")

            info = render_to_info(hass, time_since_template)
            expect(info.has_time).to_be(True)


@test
async def time_until(hass: HomeAssistant = Depends(hass)) -> None:
    """Test time_until method."""
    with patch(
        "homeassistant.helpers.template.TemplateEnvironment.is_safe_callable",
        return_value=True,
    ):
        await hass.config.async_set_time_zone("UTC")
        now = datetime.strptime("2000-01-01 10:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z")
        time_until_template = (
            '{{time_until(strptime("2000-01-01 11:00:00", "%Y-%m-%d %H:%M:%S"))}}'
        )
        with freeze_time(now):
            result = render(hass, time_until_template)
            expect(result).to_equal("1 hour")

            result = render(
                hass,
                (
                    "{{"
                    "  time_until("
                    "    strptime("
                    '        "2000-01-01 13:00:00 +01:00",'
                    '        "%Y-%m-%d %H:%M:%S %z"'
                    "    )"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("2 hours")

            result = render(
                hass,
                (
                    "{{"
                    "  time_until("
                    "    strptime("
                    '       "2000-01-01 05:00:00 -06:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"'
                    "    )"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("1 hour")

            result1 = str(
                datetime.strptime(
                    "2000-01-01 09:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z"
                )
            )
            result2 = render(
                hass,
                (
                    "{{"
                    "  time_until("
                    "    strptime("
                    '       "2000-01-01 09:00:00 +00:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"),'
                    "    precision = 2"
                    "  )"
                    "}}"
                ),
            )
            expect(result2).to_equal(result1)

            result = render(
                hass,
                (
                    "{{"
                    "  time_until("
                    "    strptime("
                    '        "2000-01-01 12:05:00 +01:00",'
                    '        "%Y-%m-%d %H:%M:%S %z"),'
                    "       precision=2"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("1 hour 5 minutes")

            result = render(
                hass,
                (
                    "{{"
                    "  time_until("
                    "    strptime("
                    '       "2000-01-01 05:54:33 -06:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"),'
                    "       precision = 3"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("1 hour 54 minutes 33 seconds")
            result = render(
                hass,
                (
                    "{{"
                    "  time_until("
                    "    strptime("
                    '       "2000-01-01 05:54:33 -06:00",'
                    '       "%Y-%m-%d %H:%M:%S %z")'
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("2 hours")
            result = render(
                hass,
                (
                    "{{"
                    "  time_until("
                    "    strptime("
                    '       "2001-02-01 05:54:33 -06:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"),'
                    "       precision = 0"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal(
                "1 year 1 month 2 days 1 hour 54 minutes 33 seconds"
            )
            result = render(
                hass,
                (
                    "{{"
                    "  time_until("
                    "    strptime("
                    '       "2001-02-01 05:54:33 -06:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"),'
                    "       precision = 4"
                    "  )"
                    "}}"
                ),
            )
            expect(result).to_equal("1 year 1 month 2 days 2 hours")
            result1 = str(
                datetime.strptime(
                    "2000-01-01 09:00:00 +00:00", "%Y-%m-%d %H:%M:%S %z"
                )
            )
            result2 = render(
                hass,
                (
                    "{{"
                    "  time_until("
                    "    strptime("
                    '       "2000-01-01 09:00:00 +00:00",'
                    '       "%Y-%m-%d %H:%M:%S %z"),'
                    "       precision=3"
                    "  )"
                    "}}"
                ),
            )
            expect(result2).to_equal(result1)

            result = render(hass, '{{time_until("string")}}')
            expect(result).to_equal("string")

            info = render_to_info(hass, time_until_template)
            expect(info.has_time).to_be(True)
