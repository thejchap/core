"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def manual_update_entity() -> None:
    """Stub for test_manual_update_entity."""

