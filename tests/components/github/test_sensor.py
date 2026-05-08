"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_updates_with_empty_release_array() -> None:
    """Stub for test_sensor_updates_with_empty_release_array."""

