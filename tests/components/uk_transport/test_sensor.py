"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def bus() -> None:
    """Stub for test_bus (port deferred)."""

@test.skip("pending tryke port")
async def train() -> None:
    """Stub for test_train (port deferred)."""
