"""Tryke skip stub for test_reproduce_state.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reproduce_group() -> None:
    """Stub for test_reproduce_group."""

