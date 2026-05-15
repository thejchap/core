"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def device_exists() -> None:
    """Stub for test_device_exists (port deferred)."""

@test.skip("pending tryke port")
async def remote_start() -> None:
    """Stub for test_remote_start (port deferred)."""

@test.skip("pending tryke port")
async def remote_stop() -> None:
    """Stub for test_remote_stop (port deferred)."""

@test.skip("pending tryke port")
async def remote_start_fails() -> None:
    """Stub for test_remote_start_fails (port deferred)."""

@test.skip("pending tryke port")
async def remote_start_exception() -> None:
    """Stub for test_remote_start_exception (port deferred)."""

@test.skip("pending tryke port")
async def remote_stop_fails() -> None:
    """Stub for test_remote_stop_fails (port deferred)."""

@test.skip("pending tryke port")
async def remote_stop_exception() -> None:
    """Stub for test_remote_stop_exception (port deferred)."""

@test.skip("pending tryke port")
async def no_buttons_without_remote_start() -> None:
    """Stub for test_no_buttons_without_remote_start (port deferred)."""
