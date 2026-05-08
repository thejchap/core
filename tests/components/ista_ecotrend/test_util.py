"""Tryke skip-stubs for test_util.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def as_number() -> None:
    """Stub for test_as_number."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def last_day_of_month() -> None:
    """Stub for test_last_day_of_month."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def get_values_by_type() -> None:
    """Stub for test_get_values_by_type."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def get_native_value() -> None:
    """Stub for test_get_native_value."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def get_statistics() -> None:
    """Stub for test_get_statistics."""
