"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def network_speed() -> None:
    """Stub for test_network_speed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def call() -> None:
    """Stub for test_call."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def disk() -> None:
    """Stub for test_disk."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def battery() -> None:
    """Stub for test_battery."""

