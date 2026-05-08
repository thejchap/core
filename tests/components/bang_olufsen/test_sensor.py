"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def battery_level() -> None:
    """Stub for test_battery_level."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remote_battery_level() -> None:
    """Stub for test_remote_battery_level."""

