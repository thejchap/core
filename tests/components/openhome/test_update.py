"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def not_supported() -> None:
    """Stub for test_not_supported (port deferred)."""

@test.skip("pending tryke port")
async def on_latest_firmware() -> None:
    """Stub for test_on_latest_firmware (port deferred)."""

@test.skip("pending tryke port")
async def update_available() -> None:
    """Stub for test_update_available (port deferred)."""

@test.skip("pending tryke port")
async def firmware_update_not_required() -> None:
    """Stub for test_firmware_update_not_required (port deferred)."""
