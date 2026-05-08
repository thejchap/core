"""Tryke skip-stubs for test_sensor.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def create_sensors() -> None:
    """Stub for test_create_sensors."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def exception_on_polling() -> None:
    """Stub for test_exception_on_polling."""
