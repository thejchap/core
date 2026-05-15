"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_retry() -> None:
    """Stub for test_setup_retry (port deferred)."""

@test.skip("pending tryke port")
async def cleanup_on_shutdown() -> None:
    """Stub for test_cleanup_on_shutdown (port deferred)."""

@test.skip("pending tryke port")
async def cleanup_on_failed_first_update() -> None:
    """Stub for test_cleanup_on_failed_first_update (port deferred)."""

@test.skip("pending tryke port")
async def wrong_device_now_has_our_ip() -> None:
    """Stub for test_wrong_device_now_has_our_ip (port deferred)."""

@test.skip("pending tryke port")
async def reload_on_title_change() -> None:
    """Stub for test_reload_on_title_change (port deferred)."""
