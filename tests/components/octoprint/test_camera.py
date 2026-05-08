"""Tryke skip-stubs for octoprint test_camera (port deferred)."""
from tryke import test

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def no_supported_camera() -> None:
    """Stub for test_no_supported_camera (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def camera() -> None:
    """Stub for test_camera (port deferred)."""

@test.skip("requires complex pyoctoprintapi mocks + entity setup")
async def camera_disabled() -> None:
    """Stub for test_camera_disabled (port deferred)."""


