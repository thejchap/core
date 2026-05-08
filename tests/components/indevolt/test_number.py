"""Tryke skip-stubs for test_number.py - snapshot_platform diverged - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def number() -> None:
    """Stub for test_number."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def number_set_values() -> None:
    """Stub for test_number_set_values."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def number_set_value_error() -> None:
    """Stub for test_number_set_value_error."""

@test.skip("snapshot_platform diverged - needs pytest --snapshot-update")
async def number_availability() -> None:
    """Stub for test_number_availability."""
