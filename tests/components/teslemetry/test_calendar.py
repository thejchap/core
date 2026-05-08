"""Tryke skip-stubs for teslemetry/test_calendar.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def calendar() -> None:
    """Stub for test_calendar."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def calendar_events() -> None:
    """Stub for test_calendar_events."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def calendar_week_crossing() -> None:
    """Stub for test_calendar_week_crossing."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def calendar_week_crossing_excluded_day() -> None:
    """Stub for test_calendar_week_crossing_excluded_day."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def calendar_multi_season() -> None:
    """Stub for test_calendar_multi_season."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def calendar_no_tariff_data() -> None:
    """Stub for test_calendar_no_tariff_data."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def calendar_invalid_season_data() -> None:
    """Stub for test_calendar_invalid_season_data."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def calendar_week_crossing_get_events() -> None:
    """Stub for test_calendar_week_crossing_get_events."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def calendar_midnight_crossing_local_start() -> None:
    """Stub for test_calendar_midnight_crossing_local_start."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def calendar_invalid_price() -> None:
    """Stub for test_calendar_invalid_price."""

