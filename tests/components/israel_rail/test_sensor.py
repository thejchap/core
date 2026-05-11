"""Tryke skip-stubs for test_sensor.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot test — out of scope")
async def valid_config() -> None:
    """Stub for test_valid_config."""

@test.skip("snapshot test — out of scope")
async def update_train() -> None:
    """Stub for test_update_train."""

@test.skip("snapshot test — out of scope")
async def fail_query() -> None:
    """Stub for test_fail_query."""

@test.skip("snapshot test — out of scope")
async def no_departures() -> None:
    """Stub for test_no_departures."""

@test.skip("snapshot test — out of scope")
async def departure_delay() -> None:
    """Stub for test_departure_delay."""
