"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def invalid_platform() -> None:
    """Stub for test_invalid_platform (port deferred)."""

@test.skip("pending tryke port")
async def platform_setup_with_error() -> None:
    """Stub for test_platform_setup_with_error (port deferred)."""
