"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def validator() -> None:
    """Stub for test_validator (port deferred)."""

@test.skip("pending tryke port")
async def validator_allow_empty() -> None:
    """Stub for test_validator_allow_empty (port deferred)."""
