"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def no_update() -> None:
    """Stub for test_no_update (port deferred)."""

@test.skip("pending tryke port")
async def update_str() -> None:
    """Stub for test_update_str (port deferred)."""

@test.skip("pending tryke port")
async def update_firm() -> None:
    """Stub for test_update_firm (port deferred)."""

@test.skip("pending tryke port")
async def update_firm_keeps_available() -> None:
    """Stub for test_update_firm_keeps_available (port deferred)."""

@test.skip("pending tryke port")
async def external_firmware_update_detected() -> None:
    """Stub for test_external_firmware_update_detected (port deferred)."""
