"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_config() -> None:
    """Stub for test_setup_config (port deferred)."""

@test.skip("pending tryke port")
async def reload_service() -> None:
    """Stub for test_reload_service (port deferred)."""
