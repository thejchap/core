"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_updates_on_hour_tick() -> None:
    """Stub for test_sensor_updates_on_hour_tick."""

