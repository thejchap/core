"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_full() -> None:
    """Stub for test_setup_full (port deferred)."""

@test.skip("pending tryke port")
async def setup_without_optional() -> None:
    """Stub for test_setup_without_optional (port deferred)."""

@test.skip("pending tryke port")
async def bad_config() -> None:
    """Stub for test_bad_config (port deferred)."""
