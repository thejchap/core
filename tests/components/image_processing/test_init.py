"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_component() -> None:
    """Stub for test_setup_component (port deferred)."""

@test.skip("pending tryke port")
async def setup_component_with_service() -> None:
    """Stub for test_setup_component_with_service (port deferred)."""

@test.skip("pending tryke port")
async def get_image_from_camera() -> None:
    """Stub for test_get_image_from_camera (port deferred)."""

@test.skip("pending tryke port")
async def get_image_without_exists_camera() -> None:
    """Stub for test_get_image_without_exists_camera (port deferred)."""

@test.skip("pending tryke port")
async def face_event_call() -> None:
    """Stub for test_face_event_call (port deferred)."""

@test.skip("pending tryke port")
async def face_event_call_no_confidence() -> None:
    """Stub for test_face_event_call_no_confidence (port deferred)."""

@test.skip("pending tryke port")
async def update_missing_camera() -> None:
    """Stub for test_update_missing_camera (port deferred)."""
