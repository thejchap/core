"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def invalid_path() -> None:
    """Stub for test_invalid_path."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def valid_path() -> None:
    """Stub for test_valid_path."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_unavailable() -> None:
    """Stub for test_state_unavailable."""

