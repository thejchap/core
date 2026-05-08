"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_states() -> None:
    """Stub for test_sensor_states."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def uptime_variation() -> None:
    """Stub for test_uptime_variation."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_removed() -> None:
    """Stub for test_sensor_removed."""

