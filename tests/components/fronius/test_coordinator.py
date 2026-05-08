"""Tryke skip stub for test_coordinator.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def adaptive_update_interval() -> None:
    """Stub for test_adaptive_update_interval."""

