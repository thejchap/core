"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def capped_setup() -> None:
    """Stub for test_capped_setup (port deferred)."""

@test.skip("pending tryke port")
async def unlimited_setup() -> None:
    """Stub for test_unlimited_setup (port deferred)."""

@test.skip("pending tryke port")
async def bad_return_code() -> None:
    """Stub for test_bad_return_code (port deferred)."""

@test.skip("pending tryke port")
async def bad_json_decode() -> None:
    """Stub for test_bad_json_decode (port deferred)."""
