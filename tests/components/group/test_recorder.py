"""Tryke skip stub for test_recorder.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def exclude_attributes() -> None:
    """Stub for test_exclude_attributes."""

