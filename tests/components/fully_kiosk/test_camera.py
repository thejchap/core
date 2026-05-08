"""Tryke skip stub for test_camera.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def camera() -> None:
    """Stub for test_camera."""

