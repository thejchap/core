"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def device_exists() -> None:
    """Stub for test_device_exists (port deferred)."""

@test.skip("pending tryke port")
async def lock_cmd() -> None:
    """Stub for test_lock_cmd (port deferred)."""

@test.skip("pending tryke port")
async def unlock_cmd() -> None:
    """Stub for test_unlock_cmd (port deferred)."""

@test.skip("pending tryke port")
async def lock_cmd_fails() -> None:
    """Stub for test_lock_cmd_fails (port deferred)."""

@test.skip("pending tryke port")
async def unlock_specific_door() -> None:
    """Stub for test_unlock_specific_door (port deferred)."""

@test.skip("pending tryke port")
async def unlock_specific_door_invalid() -> None:
    """Stub for test_unlock_specific_door_invalid (port deferred)."""
