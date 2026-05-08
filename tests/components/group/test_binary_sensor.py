"""Tryke skip stub for test_binary_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def default_state() -> None:
    """Stub for test_default_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_reporting_all() -> None:
    """Stub for test_state_reporting_all."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_reporting_any() -> None:
    """Stub for test_state_reporting_any."""

