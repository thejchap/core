"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def camera() -> None:
    """Stub for test_camera (port deferred)."""

@test.skip("pending tryke port")
async def camera_no_stream_source() -> None:
    """Stub for test_camera_no_stream_source (port deferred)."""
