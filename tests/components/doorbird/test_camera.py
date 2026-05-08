"""Tryke skip stub for test_camera.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def doorbird_cameras() -> None:
    """Stub for test_doorbird_cameras."""

