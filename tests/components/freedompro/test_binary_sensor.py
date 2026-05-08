"""Tryke skip stub for test_binary_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def binary_sensor_get_state() -> None:
    """Stub for test_binary_sensor_get_state."""

