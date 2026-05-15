"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def camera() -> None:
    """Stub for test_camera (port deferred)."""

@test.skip("snapshot test - port deferred")
async def camera_disabled() -> None:
    """Stub for test_camera_disabled (port deferred)."""
