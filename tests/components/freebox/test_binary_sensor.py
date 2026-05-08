"""Tryke skip stub for test_binary_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def raid_array_degraded() -> None:
    """Stub for test_raid_array_degraded."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def home() -> None:
    """Stub for test_home."""

