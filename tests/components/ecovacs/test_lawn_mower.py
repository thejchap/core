"""Tryke skip stub for test_lawn_mower.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def lawn_mower() -> None:
    """Stub for test_lawn_mower."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def mover_services() -> None:
    """Stub for test_mover_services."""

