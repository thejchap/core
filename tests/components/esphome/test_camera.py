"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def camera_single_image() -> None:
    """Stub for test_camera_single_image (port deferred)."""

@test.skip("pending tryke port")
async def camera_single_image_unavailable_before_requested() -> None:
    """Stub for test_camera_single_image_unavailable_before_requested (port deferred)."""

@test.skip("pending tryke port")
async def camera_single_image_unavailable_during_request() -> None:
    """Stub for test_camera_single_image_unavailable_during_request (port deferred)."""

@test.skip("pending tryke port")
async def camera_stream() -> None:
    """Stub for test_camera_stream (port deferred)."""

@test.skip("pending tryke port")
async def camera_stream_unavailable() -> None:
    """Stub for test_camera_stream_unavailable (port deferred)."""

@test.skip("pending tryke port")
async def camera_stream_with_disconnection() -> None:
    """Stub for test_camera_stream_with_disconnection (port deferred)."""
