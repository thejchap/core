"""Tryke skip stub for test_coordinator.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def exeception_wrapper() -> None:
    """Stub for test_exeception_wrapper."""

