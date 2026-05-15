"""Tryke skip stub for comfoconnect sensor tests."""

from tryke import test


@test.skip("comfoconnect _shutdown cleanup races with disconnect mock under tryke")
async def sensors() -> None:
    """Stub for test_sensors (port deferred)."""
