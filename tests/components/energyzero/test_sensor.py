"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_gas_today() -> None:
    """Stub for test_no_gas_today."""

