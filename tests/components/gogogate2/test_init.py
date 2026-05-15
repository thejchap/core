"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def config_update() -> None:
    """Stub for test_config_update (port deferred)."""

@test.skip("pending tryke port")
async def config_no_update() -> None:
    """Stub for test_config_no_update (port deferred)."""

@test.skip("pending tryke port")
async def api_failure_on_startup() -> None:
    """Stub for test_api_failure_on_startup (port deferred)."""
