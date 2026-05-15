"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def config() -> None:
    """Stub for test_config (port deferred)."""

@test.skip("pending tryke port")
async def config_full() -> None:
    """Stub for test_config_full (port deferred)."""

@test.skip("pending tryke port")
async def invalid_credential() -> None:
    """Stub for test_invalid_credential (port deferred)."""

@test.skip("pending tryke port")
async def valid_credential() -> None:
    """Stub for test_valid_credential (port deferred)."""

@test.skip("pending tryke port")
async def token_timed_out() -> None:
    """Stub for test_token_timed_out (port deferred)."""
