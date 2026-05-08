"""Tryke skip stub for test_camera.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def camera_stream_source() -> None:
    """Stub for test_camera_stream_source."""

