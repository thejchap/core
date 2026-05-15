"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def hardware_info() -> None:
    """Stub for test_hardware_info (port deferred)."""

@test.skip("pending tryke port")
async def hardware_info_fail() -> None:
    """Stub for test_hardware_info_fail (port deferred)."""
