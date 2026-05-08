"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def disabled_by_default() -> None:
    """Stub for test_disabled_by_default."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def enabling_disable_by_default() -> None:
    """Stub for test_enabling_disable_by_default."""

