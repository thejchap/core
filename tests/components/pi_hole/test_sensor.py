"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def bad_data_type() -> None:
    """Stub for test_bad_data_type (port deferred)."""

@test.skip("pending tryke port")
async def bad_data_key() -> None:
    """Stub for test_bad_data_key (port deferred)."""
