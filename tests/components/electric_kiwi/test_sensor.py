"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def hop_sensors() -> None:
    """Stub for test_hop_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def account_sensors() -> None:
    """Stub for test_account_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def check_and_move_time() -> None:
    """Stub for test_check_and_move_time."""

