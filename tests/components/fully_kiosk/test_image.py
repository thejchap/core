"""Tryke skip stub for test_image.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def image() -> None:
    """Stub for test_image."""

