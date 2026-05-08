"""Tryke skip stubs for test_sensor - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def dsmr_sensor_mqtt() -> None:
    """Stub for test_dsmr_sensor_mqtt (port deferred)."""


