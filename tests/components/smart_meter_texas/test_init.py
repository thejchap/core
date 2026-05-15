"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_with_no_config() -> None:
    """Stub for test_setup_with_no_config (port deferred)."""

@test.skip("pending tryke port")
async def auth_failure() -> None:
    """Stub for test_auth_failure (port deferred)."""

@test.skip("pending tryke port")
async def api_timeout() -> None:
    """Stub for test_api_timeout (port deferred)."""

@test.skip("pending tryke port")
async def update_failure() -> None:
    """Stub for test_update_failure (port deferred)."""

@test.skip("pending tryke port")
async def unload_config_entry() -> None:
    """Stub for test_unload_config_entry (port deferred)."""
