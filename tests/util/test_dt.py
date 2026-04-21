"""Test Home Assistant date util methods."""

from __future__ import annotations

from collections.abc import Generator
from datetime import UTC, datetime, timedelta

from tryke import expect, fixture, test

from homeassistant.util import dt as dt_util

DEFAULT_TIME_ZONE = dt_util.get_default_time_zone()
TEST_TIME_ZONE = "America/Los_Angeles"


@fixture
def teardown() -> Generator[None]:
    """Stop everything that was started."""
    yield
    dt_util.set_default_time_zone(DEFAULT_TIME_ZONE)


@test
def get_time_zone_retrieves_valid_time_zone() -> None:
    """Test getting a time zone."""
    expect(dt_util.get_time_zone(TEST_TIME_ZONE)).not_.to_be(None)


@test
async def async_get_time_zone_retrieves_valid_time_zone() -> None:
    """Test getting a time zone."""
    expect(await dt_util.async_get_time_zone(TEST_TIME_ZONE)).not_.to_be(None)


@test
def get_time_zone_returns_none_for_garbage_time_zone() -> None:
    """Test getting a non existing time zone."""
    expect(dt_util.get_time_zone("Non existing time zone")).to_be(None)


@test
async def async_get_time_zone_returns_none_for_garbage_time_zone() -> None:
    """Test getting a non existing time zone."""
    expect(await dt_util.async_get_time_zone("Non existing time zone")).to_be(None)


@test
def set_default_time_zone() -> None:
    """Test setting default time zone."""
    time_zone = dt_util.get_time_zone(TEST_TIME_ZONE)

    dt_util.set_default_time_zone(time_zone)

    expect(dt_util.now().tzinfo is time_zone).to_be(True)


@test
def utcnow() -> None:
    """Test the UTC now method."""
    expect(
        abs(
            dt_util.utcnow().replace(tzinfo=None)
            - datetime.now(UTC).replace(tzinfo=None)
        )
        < timedelta(seconds=1)
    ).to_be(True)


@test
def now() -> None:
    """Test the now method."""
    dt_util.set_default_time_zone(dt_util.get_time_zone(TEST_TIME_ZONE))

    expect(
        abs(
            dt_util.as_utc(dt_util.now()).replace(tzinfo=None)
            - datetime.now(UTC).replace(tzinfo=None)
        )
        < timedelta(seconds=1)
    ).to_be(True)


@test
def as_utc_with_naive_object() -> None:
    """Test the now method."""
    utcnow = datetime.now(UTC).replace(tzinfo=None)

    expect(dt_util.as_utc(utcnow).replace(tzinfo=None)).to_equal(utcnow)


@test
def as_utc_with_utc_object() -> None:
    """Test UTC time with UTC object."""
    utcnow = dt_util.utcnow()

    expect(dt_util.as_utc(utcnow)).to_equal(utcnow)


@test
def as_utc_with_local_object() -> None:
    """Test the UTC time with local object."""
    dt_util.set_default_time_zone(dt_util.get_time_zone(TEST_TIME_ZONE))
    localnow = dt_util.now()
    utcnow = dt_util.as_utc(localnow)

    expect(utcnow).to_equal(localnow)
    expect(localnow.tzinfo != utcnow.tzinfo).to_be(True)


@test
def as_local_with_naive_object() -> None:
    """Test local time with native object."""
    now = dt_util.now()
    expect(
        abs(now - dt_util.as_local(datetime.now(UTC).replace(tzinfo=None)))
        < timedelta(seconds=1)
    ).to_be(True)


@test
def as_local_with_utc_object() -> None:
    """Test local time with UTC object."""
    dt_util.set_default_time_zone(dt_util.get_time_zone(TEST_TIME_ZONE))

    utcnow = dt_util.utcnow()
    localnow = dt_util.as_local(utcnow)

    expect(utcnow).to_equal(localnow)
    expect(localnow.tzinfo != utcnow.tzinfo).to_be(True)


@test
def utc_from_timestamp() -> None:
    """Test utc_from_timestamp method."""
    expect(dt_util.utc_from_timestamp(521251200)).to_equal(
        datetime(1986, 7, 9, tzinfo=dt_util.UTC)
    )


@test
def as_timestamp() -> None:
    """Test as_timestamp method."""
    ts = 1462401234
    utc_dt = dt_util.utc_from_timestamp(ts)
    expect(dt_util.as_timestamp(utc_dt)).to_equal(ts)
    utc_iso = utc_dt.isoformat()
    expect(dt_util.as_timestamp(utc_iso)).to_equal(ts)

    # Confirm the ability to handle a string passed in.
    delta = dt_util.as_timestamp("2016-01-01 12:12:12")
    delta -= dt_util.as_timestamp("2016-01-01 12:12:11")
    expect(delta).to_equal(1)


@test
def parse_datetime_converts_correctly() -> None:
    """Test parse_datetime converts strings."""
    expect(dt_util.parse_datetime("1986-07-09T12:00:00Z")).to_equal(
        datetime(1986, 7, 9, 12, 0, 0, tzinfo=dt_util.UTC)
    )

    utcnow = dt_util.utcnow()

    expect(dt_util.parse_datetime(utcnow.isoformat())).to_equal(utcnow)


@test
def parse_datetime_returns_none_for_incorrect_format() -> None:
    """Test parse_datetime returns None if incorrect format."""
    expect(dt_util.parse_datetime("not a datetime string")).to_be(None)


@test
def parse_datetime_raises_for_incorrect_format() -> None:
    """Test parse_datetime raises ValueError if raise_on_error is set with an incorrect format."""
    expect(
        lambda: dt_util.parse_datetime("not a datetime string", raise_on_error=True)
    ).to_raise(ValueError)


@test.cases(
    test.case("PT10M", duration_string="PT10M", expected_result=timedelta(minutes=10)),
    test.case("PT0S", duration_string="PT0S", expected_result=timedelta(0)),
    test.case(
        "P10DT11H11M01S",
        duration_string="P10DT11H11M01S",
        expected_result=timedelta(days=10, hours=11, minutes=11, seconds=1),
    ),
    test.case(
        "4 1:20:30.111111",
        duration_string="4 1:20:30.111111",
        expected_result=timedelta(
            days=4, hours=1, minutes=20, seconds=30, microseconds=111111
        ),
    ),
    test.case(
        "4 1:2:30",
        duration_string="4 1:2:30",
        expected_result=timedelta(days=4, hours=1, minutes=2, seconds=30),
    ),
    test.case(
        "3 days 04:05:06",
        duration_string="3 days 04:05:06",
        expected_result=timedelta(days=3, hours=4, minutes=5, seconds=6),
    ),
    test.case("P1YT10M", duration_string="P1YT10M", expected_result=None),
    test.case("P1MT10M", duration_string="P1MT10M", expected_result=None),
    test.case("1MT10M", duration_string="1MT10M", expected_result=None),
    test.case("P1MT100M", duration_string="P1MT100M", expected_result=None),
    test.case("P1234", duration_string="P1234", expected_result=None),
)
def parse_duration(duration_string: str, expected_result: timedelta | None) -> None:
    """Test that parse_duration returns the expected result."""
    expect(dt_util.parse_duration(duration_string)).to_equal(expected_result)


@test
def get_age() -> None:
    """Test get_age."""
    diff = dt_util.now() - timedelta(seconds=0)
    expect(dt_util.get_age(diff)).to_equal("0 seconds")
    expect(dt_util.get_age(diff, precision=2)).to_equal("0 seconds")

    diff = dt_util.now() - timedelta(seconds=1)
    expect(dt_util.get_age(diff)).to_equal("1 second")
    expect(dt_util.get_age(diff, precision=2)).to_equal("1 second")

    diff = dt_util.now() + timedelta(seconds=1)
    expect(lambda: dt_util.get_age(diff)).to_raise(ValueError)

    diff = dt_util.now() - timedelta(seconds=30)
    expect(dt_util.get_age(diff)).to_equal("30 seconds")
    diff = dt_util.now() + timedelta(seconds=30)

    diff = dt_util.now() - timedelta(minutes=5)
    expect(dt_util.get_age(diff)).to_equal("5 minutes")

    diff = dt_util.now() - timedelta(minutes=1)
    expect(dt_util.get_age(diff)).to_equal("1 minute")

    diff = dt_util.now() - timedelta(minutes=300)
    expect(dt_util.get_age(diff)).to_equal("5 hours")

    diff = dt_util.now() - timedelta(minutes=320)
    expect(dt_util.get_age(diff)).to_equal("5 hours")
    expect(dt_util.get_age(diff, precision=2)).to_equal("5 hours 20 minutes")
    expect(dt_util.get_age(diff, precision=3)).to_equal("5 hours 20 minutes")

    diff = dt_util.now() - timedelta(minutes=1.6 * 60 * 24)
    expect(dt_util.get_age(diff)).to_equal("2 days")
    expect(dt_util.get_age(diff, precision=2)).to_equal("1 day 14 hours")
    expect(dt_util.get_age(diff, precision=3)).to_equal("1 day 14 hours 24 minutes")
    diff = dt_util.now() + timedelta(minutes=1.6 * 60 * 24)
    expect(lambda: dt_util.get_age(diff)).to_raise(ValueError)

    diff = dt_util.now() - timedelta(minutes=2 * 60 * 24)
    expect(dt_util.get_age(diff)).to_equal("2 days")

    diff = dt_util.now() - timedelta(minutes=32 * 60 * 24)
    expect(dt_util.get_age(diff)).to_equal("1 month")
    expect(dt_util.get_age(diff, precision=10)).to_equal("1 month 2 days")

    diff = dt_util.now() - timedelta(minutes=32 * 60 * 24 + 1)
    expect(dt_util.get_age(diff, precision=3)).to_equal("1 month 2 days 1 minute")

    diff = dt_util.now() - timedelta(minutes=365 * 60 * 24)
    expect(dt_util.get_age(diff)).to_equal("1 year")


@test
def time_remaining() -> None:
    """Test get_age."""
    diff = dt_util.now() + timedelta(seconds=0)
    expect(dt_util.get_time_remaining(diff)).to_equal("0 seconds")
    expect(dt_util.get_time_remaining(diff)).to_equal("0 seconds")
    expect(dt_util.get_time_remaining(diff, precision=2)).to_equal("0 seconds")

    diff = dt_util.now() + timedelta(seconds=1)
    expect(dt_util.get_time_remaining(diff)).to_equal("1 second")

    diff = dt_util.now() - timedelta(seconds=1)
    expect(lambda: dt_util.get_time_remaining(diff)).to_raise(ValueError)

    diff = dt_util.now() + timedelta(seconds=30)
    expect(dt_util.get_time_remaining(diff)).to_equal("30 seconds")

    diff = dt_util.now() + timedelta(minutes=5)
    expect(dt_util.get_time_remaining(diff)).to_equal("5 minutes")

    diff = dt_util.now() + timedelta(minutes=1)
    expect(dt_util.get_time_remaining(diff)).to_equal("1 minute")

    diff = dt_util.now() + timedelta(minutes=300)
    expect(dt_util.get_time_remaining(diff)).to_equal("5 hours")

    diff = dt_util.now() + timedelta(minutes=320)
    expect(dt_util.get_time_remaining(diff)).to_equal("5 hours")
    expect(dt_util.get_time_remaining(diff, precision=2)).to_equal("5 hours 20 minutes")
    expect(dt_util.get_time_remaining(diff, precision=3)).to_equal("5 hours 20 minutes")

    diff = dt_util.now() + timedelta(minutes=1.6 * 60 * 24)
    expect(dt_util.get_time_remaining(diff)).to_equal("2 days")
    expect(dt_util.get_time_remaining(diff, precision=2)).to_equal("1 day 14 hours")
    expect(dt_util.get_time_remaining(diff, precision=3)).to_equal(
        "1 day 14 hours 24 minutes"
    )
    diff = dt_util.now() - timedelta(minutes=1.6 * 60 * 24)
    expect(lambda: dt_util.get_time_remaining(diff)).to_raise(ValueError)

    diff = dt_util.now() + timedelta(minutes=2 * 60 * 24)
    expect(dt_util.get_time_remaining(diff)).to_equal("2 days")

    diff = dt_util.now() + timedelta(minutes=32 * 60 * 24)
    expect(dt_util.get_time_remaining(diff)).to_equal("1 month")
    expect(dt_util.get_time_remaining(diff, precision=10)).to_equal("1 month 2 days")

    diff = dt_util.now() + timedelta(minutes=32 * 60 * 24 + 1)
    expect(dt_util.get_time_remaining(diff, precision=3)).to_equal(
        "1 month 2 days 1 minute"
    )

    diff = dt_util.now() + timedelta(minutes=365 * 60 * 24)
    expect(dt_util.get_time_remaining(diff)).to_equal("1 year")


@test
def parse_time_expression() -> None:
    """Test parse_time_expression."""
    expect(dt_util.parse_time_expression("*", 0, 59)).to_equal(list(range(60)))
    expect(dt_util.parse_time_expression(None, 0, 59)).to_equal(list(range(60)))

    expect(dt_util.parse_time_expression("/5", 0, 59)).to_equal(list(range(0, 60, 5)))

    expect(dt_util.parse_time_expression("/4", 5, 20)).to_equal([8, 12, 16, 20])
    expect(dt_util.parse_time_expression("/10", 10, 30)).to_equal([10, 20, 30])
    expect(dt_util.parse_time_expression("/3", 4, 29)).to_equal(
        [6, 9, 12, 15, 18, 21, 24, 27]
    )

    expect(dt_util.parse_time_expression([2, 1, 3], 0, 59)).to_equal([1, 2, 3])

    expect(dt_util.parse_time_expression("*", 0, 23)).to_equal(list(range(24)))

    expect(dt_util.parse_time_expression(42, 0, 59)).to_equal([42])
    expect(dt_util.parse_time_expression("42", 0, 59)).to_equal([42])

    expect(lambda: dt_util.parse_time_expression(61, 0, 60)).to_raise(ValueError)


@test
def find_next_time_expression_time_basic() -> None:
    """Test basic stuff for find_next_time_expression_time."""

    def find(dt, hour, minute, second):
        """Call test_find_next_time_expression_time."""
        seconds = dt_util.parse_time_expression(second, 0, 59)
        minutes = dt_util.parse_time_expression(minute, 0, 59)
        hours = dt_util.parse_time_expression(hour, 0, 23)

        return dt_util.find_next_time_expression_time(dt, seconds, minutes, hours)

    expect(find(datetime(2018, 10, 7, 10, 20, 0), "*", "/30", 0)).to_equal(
        datetime(2018, 10, 7, 10, 30, 0)
    )

    expect(find(datetime(2018, 10, 7, 10, 30, 0), "*", "/30", 0)).to_equal(
        datetime(2018, 10, 7, 10, 30, 0)
    )

    expect(find(datetime(2018, 10, 7, 10, 30, 0), "/3", "/30", [30, 45])).to_equal(
        datetime(2018, 10, 7, 12, 0, 30)
    )

    expect(find(datetime(2018, 10, 7, 10, 30, 0), 5, 0, 0)).to_equal(
        datetime(2018, 10, 8, 5, 0, 0)
    )

    expect(find(datetime(2018, 10, 7, 10, 30, 0, 999999), "*", "/30", 0)).to_equal(
        datetime(2018, 10, 7, 10, 30, 0)
    )


@test
def find_next_time_expression_time_dst() -> None:
    """Test daylight saving time for find_next_time_expression_time."""
    tz = dt_util.get_time_zone("Europe/Vienna")
    dt_util.set_default_time_zone(tz)

    def find(dt, hour, minute, second) -> datetime:
        """Call test_find_next_time_expression_time."""
        seconds = dt_util.parse_time_expression(second, 0, 59)
        minutes = dt_util.parse_time_expression(minute, 0, 59)
        hours = dt_util.parse_time_expression(hour, 0, 23)

        local = dt_util.find_next_time_expression_time(dt, seconds, minutes, hours)
        return dt_util.as_utc(local)

    # Entering DST, clocks are rolled forward.
    expect(find(datetime(2018, 3, 25, 1, 50, 0, tzinfo=tz), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2018, 3, 26, 2, 30, 0, tzinfo=tz))
    )

    expect(find(datetime(2018, 3, 25, 3, 50, 0, tzinfo=tz), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2018, 3, 26, 2, 30, 0, tzinfo=tz))
    )

    expect(find(datetime(2018, 3, 26, 1, 50, 0, tzinfo=tz), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2018, 3, 26, 2, 30, 0, tzinfo=tz))
    )

    # Leaving DST, clocks are rolled back.
    expect(find(datetime(2018, 10, 28, 2, 5, 0, tzinfo=tz, fold=0), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2018, 10, 28, 2, 30, 0, tzinfo=tz, fold=0))
    )

    expect(find(datetime(2018, 10, 28, 2, 5, 0, tzinfo=tz), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2018, 10, 28, 2, 30, 0, tzinfo=tz, fold=0))
    )

    expect(find(datetime(2018, 10, 28, 2, 55, 0, tzinfo=tz), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2018, 10, 28, 2, 30, 0, tzinfo=tz, fold=1))
    )

    expect(
        find(datetime(2018, 10, 28, 2, 55, 0, tzinfo=tz, fold=0), 2, 30, 0)
    ).to_equal(dt_util.as_utc(datetime(2018, 10, 28, 2, 30, 0, tzinfo=tz, fold=1)))

    expect(
        find(datetime(2018, 10, 28, 2, 55, 0, tzinfo=tz, fold=1), 4, 30, 0)
    ).to_equal(dt_util.as_utc(datetime(2018, 10, 28, 4, 30, 0, tzinfo=tz, fold=0)))

    expect(find(datetime(2018, 10, 28, 2, 5, 0, tzinfo=tz, fold=1), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2018, 10, 28, 2, 30, 0, tzinfo=tz, fold=1))
    )

    expect(
        find(datetime(2018, 10, 28, 2, 55, 0, tzinfo=tz, fold=0), 2, 30, 0)
    ).to_equal(dt_util.as_utc(datetime(2018, 10, 28, 2, 30, 0, tzinfo=tz, fold=1)))


# DST begins on 2021.03.28 2:00, clocks were turned forward 1h; 2:00-3:00 time does not exist.
@test.cases(
    test.case(
        "00:00-2:30",
        now_dt=datetime(2021, 3, 28, 0, 0, 0),
        expected_dt=datetime(2021, 3, 29, 2, 30, 0),
    ),
)
def find_next_time_expression_entering_dst(
    now_dt: datetime, expected_dt: datetime
) -> None:
    """Test entering daylight saving time for find_next_time_expression_time."""
    tz = dt_util.get_time_zone("Europe/Vienna")
    dt_util.set_default_time_zone(tz)
    # Match on 02:30:00 every day.
    pattern_seconds = dt_util.parse_time_expression(0, 0, 59)
    pattern_minutes = dt_util.parse_time_expression(30, 0, 59)
    pattern_hours = dt_util.parse_time_expression(2, 0, 59)

    now_dt = now_dt.replace(tzinfo=tz)
    expected_dt = expected_dt.replace(tzinfo=tz)

    res_dt = dt_util.find_next_time_expression_time(
        now_dt, pattern_seconds, pattern_minutes, pattern_hours
    )
    expect(dt_util.as_utc(res_dt)).to_equal(dt_util.as_utc(expected_dt))


# DST ends on 2021.10.31 2:00, clocks were turned backward 1h; 2:00-3:00 time is ambiguous.
@test.cases(
    test.case(
        "00:00-2:30",
        now_dt=datetime(2021, 10, 31, 0, 0, 0),
        expected_dt=datetime(2021, 10, 31, 2, 30, 0, fold=0),
    ),
    test.case(
        "02:00f0-2:30f0",
        now_dt=datetime(2021, 10, 31, 2, 0, 0, fold=0),
        expected_dt=datetime(2021, 10, 31, 2, 30, 0, fold=0),
    ),
    test.case(
        "02:15f0-2:30f0",
        now_dt=datetime(2021, 10, 31, 2, 15, 0, fold=0),
        expected_dt=datetime(2021, 10, 31, 2, 30, 0, fold=0),
    ),
    test.case(
        "02:30:00f0-2:30f1",
        now_dt=datetime(2021, 10, 31, 2, 30, 0, fold=0),
        expected_dt=datetime(2021, 10, 31, 2, 30, 0, fold=0),
    ),
    test.case(
        "02:30:01f0-2:30f1",
        now_dt=datetime(2021, 10, 31, 2, 30, 1, fold=0),
        expected_dt=datetime(2021, 10, 31, 2, 30, 0, fold=1),
    ),
    test.case(
        "02:45f0-2:30f1",
        now_dt=datetime(2021, 10, 31, 2, 45, 0, fold=0),
        expected_dt=datetime(2021, 10, 31, 2, 30, 0, fold=1),
    ),
    test.case(
        "02:00f1-2:30f1",
        now_dt=datetime(2021, 10, 31, 2, 0, 0, fold=1),
        expected_dt=datetime(2021, 10, 31, 2, 30, 0, fold=1),
    ),
    test.case(
        "02:15f1-2:30f1",
        now_dt=datetime(2021, 10, 31, 2, 15, 0, fold=1),
        expected_dt=datetime(2021, 10, 31, 2, 30, 0, fold=1),
    ),
    test.case(
        "02:30:00f1-2:30f1",
        now_dt=datetime(2021, 10, 31, 2, 30, 0, fold=1),
        expected_dt=datetime(2021, 10, 31, 2, 30, 0, fold=1),
    ),
    test.case(
        "02:30:01f1-next-day",
        now_dt=datetime(2021, 10, 31, 2, 30, 1, fold=1),
        expected_dt=datetime(2021, 11, 1, 2, 30, 0),
    ),
    test.case(
        "02:45f1-next-day",
        now_dt=datetime(2021, 10, 31, 2, 45, 0, fold=1),
        expected_dt=datetime(2021, 11, 1, 2, 30, 0),
    ),
    test.case(
        "08:00f1-next-day",
        now_dt=datetime(2021, 10, 31, 8, 0, 1),
        expected_dt=datetime(2021, 11, 1, 2, 30, 0),
    ),
)
def find_next_time_expression_exiting_dst(
    now_dt: datetime, expected_dt: datetime
) -> None:
    """Test exiting daylight saving time for find_next_time_expression_time."""
    tz = dt_util.get_time_zone("Europe/Vienna")
    dt_util.set_default_time_zone(tz)
    # Match on 02:30:00 every day.
    pattern_seconds = dt_util.parse_time_expression(0, 0, 59)
    pattern_minutes = dt_util.parse_time_expression(30, 0, 59)
    pattern_hours = dt_util.parse_time_expression(2, 0, 59)

    now_dt = now_dt.replace(tzinfo=tz)
    expected_dt = expected_dt.replace(tzinfo=tz)

    res_dt = dt_util.find_next_time_expression_time(
        now_dt, pattern_seconds, pattern_minutes, pattern_hours
    )
    expect(dt_util.as_utc(res_dt)).to_equal(dt_util.as_utc(expected_dt))


@test
def find_next_time_expression_time_dst_chicago() -> None:
    """Test daylight saving time for find_next_time_expression_time."""
    tz = dt_util.get_time_zone("America/Chicago")
    dt_util.set_default_time_zone(tz)

    def find(dt, hour, minute, second) -> datetime:
        """Call test_find_next_time_expression_time."""
        seconds = dt_util.parse_time_expression(second, 0, 59)
        minutes = dt_util.parse_time_expression(minute, 0, 59)
        hours = dt_util.parse_time_expression(hour, 0, 23)

        local = dt_util.find_next_time_expression_time(dt, seconds, minutes, hours)
        return dt_util.as_utc(local)

    # Entering DST, clocks are rolled forward.
    expect(find(datetime(2021, 3, 14, 1, 50, 0, tzinfo=tz), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 3, 15, 2, 30, 0, tzinfo=tz))
    )

    expect(find(datetime(2021, 3, 14, 3, 50, 0, tzinfo=tz), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 3, 15, 2, 30, 0, tzinfo=tz))
    )

    expect(find(datetime(2021, 3, 14, 1, 50, 0, tzinfo=tz), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 3, 15, 2, 30, 0, tzinfo=tz))
    )

    expect(find(datetime(2021, 3, 14, 1, 50, 0, tzinfo=tz), 3, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 3, 14, 3, 30, 0, tzinfo=tz))
    )

    # Leaving DST, clocks are rolled back.
    expect(find(datetime(2021, 11, 7, 2, 5, 0, tzinfo=tz, fold=0), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz, fold=0))
    )

    expect(find(datetime(2021, 11, 7, 2, 5, 0, tzinfo=tz), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz))
    )

    expect(find(datetime(2021, 11, 7, 2, 5, 0, tzinfo=tz), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz, fold=0))
    )

    expect(find(datetime(2021, 11, 7, 2, 10, 0, tzinfo=tz), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz, fold=1))
    )

    expect(find(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz, fold=0), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz, fold=1))
    )

    expect(find(datetime(2021, 11, 7, 2, 55, 0, tzinfo=tz, fold=0), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 11, 8, 2, 30, 0, tzinfo=tz, fold=1))
    )

    expect(find(datetime(2021, 11, 7, 2, 55, 0, tzinfo=tz, fold=1), 4, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 11, 7, 4, 30, 0, tzinfo=tz, fold=0))
    )

    expect(find(datetime(2021, 11, 7, 2, 5, 0, tzinfo=tz, fold=1), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 11, 7, 2, 30, 0, tzinfo=tz, fold=1))
    )

    expect(find(datetime(2021, 11, 7, 2, 55, 0, tzinfo=tz, fold=0), 2, 30, 0)).to_equal(
        dt_util.as_utc(datetime(2021, 11, 8, 2, 30, 0, tzinfo=tz))
    )


def _get_matches(hours, minutes, seconds):
    matching_hours = dt_util.parse_time_expression(hours, 0, 23)
    matching_minutes = dt_util.parse_time_expression(minutes, 0, 59)
    matching_seconds = dt_util.parse_time_expression(seconds, 0, 59)
    return matching_hours, matching_minutes, matching_seconds


@test
def find_next_time_expression_day_before_dst_change_the_same_time() -> None:
    """Test the day before DST to establish behavior without DST."""
    tz = dt_util.get_time_zone("America/Chicago")
    dt_util.set_default_time_zone(tz)

    # Not in DST yet.
    hour_minute_second = (12, 30, 1)
    test_time = datetime(2021, 10, 7, *hour_minute_second, tzinfo=tz, fold=0)
    matching_hours, matching_minutes, matching_seconds = _get_matches(
        *hour_minute_second
    )
    next_time = dt_util.find_next_time_expression_time(
        test_time, matching_seconds, matching_minutes, matching_hours
    )
    expect(next_time).to_equal(
        datetime(2021, 10, 7, *hour_minute_second, tzinfo=tz, fold=0)
    )
    expect(next_time.fold).to_equal(0)
    expect(dt_util.as_utc(next_time)).to_equal(
        datetime(2021, 10, 7, 17, 30, 1, tzinfo=dt_util.UTC)
    )


@test
def find_next_time_expression_time_leave_dst_chicago_before_the_fold_30_s() -> None:
    """Test leaving daylight saving time for find_next_time_expression_time 30s into the future."""
    tz = dt_util.get_time_zone("America/Chicago")
    dt_util.set_default_time_zone(tz)

    # Leaving DST, clocks are rolled back.

    # Move ahead 30 seconds not folded yet.
    hour_minute_second = (1, 30, 31)
    test_time = datetime(2021, 11, 7, 1, 30, 1, tzinfo=tz, fold=0)
    matching_hours, matching_minutes, matching_seconds = _get_matches(
        *hour_minute_second
    )
    next_time = dt_util.find_next_time_expression_time(
        test_time, matching_seconds, matching_minutes, matching_hours
    )
    expect(next_time).to_equal(datetime(2021, 11, 7, 1, 30, 31, tzinfo=tz, fold=0))
    expect(dt_util.as_utc(next_time)).to_equal(
        datetime(2021, 11, 7, 6, 30, 31, tzinfo=dt_util.UTC)
    )
    expect(next_time.fold).to_equal(0)


@test
def find_next_time_expression_time_leave_dst_chicago_before_the_fold_same_time() -> (
    None
):
    """Test leaving daylight saving time for find_next_time_expression_time with the same time."""
    tz = dt_util.get_time_zone("America/Chicago")
    dt_util.set_default_time_zone(tz)

    # Leaving DST, clocks are rolled back.

    # Move to the same time not folded yet.
    hour_minute_second = (0, 30, 1)
    test_time = datetime(2021, 11, 7, *hour_minute_second, tzinfo=tz, fold=0)
    matching_hours, matching_minutes, matching_seconds = _get_matches(
        *hour_minute_second
    )
    next_time = dt_util.find_next_time_expression_time(
        test_time, matching_seconds, matching_minutes, matching_hours
    )
    expect(next_time).to_equal(
        datetime(2021, 11, 7, *hour_minute_second, tzinfo=tz, fold=0)
    )
    expect(dt_util.as_utc(next_time)).to_equal(
        datetime(2021, 11, 7, 5, 30, 1, tzinfo=dt_util.UTC)
    )
    expect(next_time.fold).to_equal(0)


@test
def find_next_time_expression_time_leave_dst_chicago_into_the_fold_same_time() -> None:
    """Test leaving daylight saving time for find_next_time_expression_time."""
    tz = dt_util.get_time_zone("America/Chicago")
    dt_util.set_default_time_zone(tz)

    # Leaving DST, clocks are rolled back.

    # Find the same time inside the fold.
    hour_minute_second = (1, 30, 1)
    test_time = datetime(2021, 11, 7, *hour_minute_second, tzinfo=tz, fold=0)
    matching_hours, matching_minutes, matching_seconds = _get_matches(
        *hour_minute_second
    )

    next_time = dt_util.find_next_time_expression_time(
        test_time, matching_seconds, matching_minutes, matching_hours
    )
    expect(next_time).to_equal(
        datetime(2021, 11, 7, *hour_minute_second, tzinfo=tz, fold=1)
    )
    expect(next_time.fold).to_equal(0)
    expect(dt_util.as_utc(next_time)).to_equal(
        datetime(2021, 11, 7, 6, 30, 1, tzinfo=dt_util.UTC)
    )


@test
def find_next_time_expression_time_leave_dst_chicago_into_the_fold_ahead_1_hour_10_min() -> (
    None
):
    """Test leaving daylight saving time for find_next_time_expression_time."""
    tz = dt_util.get_time_zone("America/Chicago")
    dt_util.set_default_time_zone(tz)

    # Leaving DST, clocks are rolled back.

    # Find 1h 10m after into the fold.
    # Start at 01:30:01 fold=0.
    # Reach to 01:20:01 fold=1.
    hour_minute_second = (1, 20, 1)
    test_time = datetime(2021, 11, 7, 1, 30, 1, tzinfo=tz, fold=0)
    matching_hours, matching_minutes, matching_seconds = _get_matches(
        *hour_minute_second
    )

    next_time = dt_util.find_next_time_expression_time(
        test_time, matching_seconds, matching_minutes, matching_hours
    )
    expect(next_time).to_equal(
        datetime(2021, 11, 7, *hour_minute_second, tzinfo=tz, fold=1)
    )
    expect(next_time.fold).to_equal(1)  # Time is ambiguous.
    expect(dt_util.as_utc(next_time)).to_equal(
        datetime(2021, 11, 7, 7, 20, 1, tzinfo=dt_util.UTC)
    )


@test
def find_next_time_expression_time_leave_dst_chicago_inside_the_fold_ahead_10_min() -> (
    None
):
    """Test leaving daylight saving time for find_next_time_expression_time."""
    tz = dt_util.get_time_zone("America/Chicago")
    dt_util.set_default_time_zone(tz)

    # Leaving DST, clocks are rolled back.

    # Find 10m later while we are in the fold.
    # Start at 01:30:01 fold=0.
    # Reach to 01:40:01 fold=1.
    hour_minute_second = (1, 40, 1)
    test_time = datetime(2021, 11, 7, 1, 30, 1, tzinfo=tz, fold=1)
    matching_hours, matching_minutes, matching_seconds = _get_matches(
        *hour_minute_second
    )

    next_time = dt_util.find_next_time_expression_time(
        test_time, matching_seconds, matching_minutes, matching_hours
    )
    expect(next_time).to_equal(
        datetime(2021, 11, 7, *hour_minute_second, tzinfo=tz, fold=1)
    )
    expect(next_time.fold).to_equal(1)  # Time is ambiguous.
    expect(dt_util.as_utc(next_time)).to_equal(
        datetime(2021, 11, 7, 7, 40, 1, tzinfo=dt_util.UTC)
    )


@test
def find_next_time_expression_time_leave_dst_chicago_past_the_fold_ahead_2_hour_10_min() -> (
    None
):
    """Test leaving daylight saving time for find_next_time_expression_time."""
    tz = dt_util.get_time_zone("America/Chicago")
    dt_util.set_default_time_zone(tz)

    # Leaving DST, clocks are rolled back.

    # Find 1h 10m after into the fold.
    # Start at 01:30:01 fold=0.
    # Reach to 02:20:01 past the fold.
    hour_minute_second = (2, 20, 1)
    test_time = datetime(2021, 11, 7, 1, 30, 1, tzinfo=tz, fold=0)
    matching_hours, matching_minutes, matching_seconds = _get_matches(
        *hour_minute_second
    )

    next_time = dt_util.find_next_time_expression_time(
        test_time, matching_seconds, matching_minutes, matching_hours
    )
    expect(next_time).to_equal(
        datetime(2021, 11, 7, *hour_minute_second, tzinfo=tz, fold=1)
    )
    expect(next_time.fold).to_equal(0)  # Time is no longer ambiguous.
    expect(dt_util.as_utc(next_time)).to_equal(
        datetime(2021, 11, 7, 8, 20, 1, tzinfo=dt_util.UTC)
    )


@test
def find_next_time_expression_microseconds() -> None:
    """Test finding next time expression with microsecond clock drift."""
    hour_minute_second = (None, "5", "10")
    test_time = datetime(2022, 5, 13, 0, 5, 9, tzinfo=dt_util.UTC)
    matching_hours, matching_minutes, matching_seconds = _get_matches(
        *hour_minute_second
    )
    next_time = dt_util.find_next_time_expression_time(
        test_time, matching_seconds, matching_minutes, matching_hours
    )
    expect(next_time).to_equal(datetime(2022, 5, 13, 0, 5, 10, tzinfo=dt_util.UTC))
    next_time_last_microsecond_plus_one = next_time.replace(
        microsecond=999999
    ) + timedelta(seconds=1)
    time_after = dt_util.find_next_time_expression_time(
        next_time_last_microsecond_plus_one,
        matching_seconds,
        matching_minutes,
        matching_hours,
    )
    expect(time_after).to_equal(datetime(2022, 5, 13, 1, 5, 10, tzinfo=dt_util.UTC))


@test
def find_next_time_expression_tenth_second_pattern_does_not_drift_entering_dst() -> (
    None
):
    """Test finding next time expression tenth second pattern does not drift entering dst."""
    tz = dt_util.get_time_zone("America/Chicago")
    dt_util.set_default_time_zone(tz)
    tenth_second_pattern = (None, None, "10")
    # Entering DST, clocks go forward.
    test_time = datetime(2021, 3, 15, 2, 30, 0, tzinfo=tz, fold=0)
    matching_hours, matching_minutes, matching_seconds = _get_matches(
        *tenth_second_pattern
    )
    next_time = dt_util.find_next_time_expression_time(
        test_time, matching_seconds, matching_minutes, matching_hours
    )
    expect(next_time).to_equal(datetime(2021, 3, 15, 2, 30, 10, tzinfo=tz))
    prev_target = next_time
    for _ in range(1000):
        next_target = dt_util.find_next_time_expression_time(
            prev_target.replace(microsecond=999999) + timedelta(seconds=1),
            matching_seconds,
            matching_minutes,
            matching_hours,
        )
        expect((next_target - prev_target).total_seconds()).to_equal(60)
        expect(next_target.second).to_equal(10)
        prev_target = next_target
