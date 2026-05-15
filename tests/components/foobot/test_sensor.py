"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def default_setup() -> None:
    """Stub for test_default_setup (port deferred)."""

@test.skip("pending tryke port")
async def setup_timeout_error() -> None:
    """Stub for test_setup_timeout_error (port deferred)."""

@test.skip("pending tryke port")
async def setup_permanent_error() -> None:
    """Stub for test_setup_permanent_error (port deferred)."""

@test.skip("pending tryke port")
async def setup_temporary_error() -> None:
    """Stub for test_setup_temporary_error (port deferred)."""
