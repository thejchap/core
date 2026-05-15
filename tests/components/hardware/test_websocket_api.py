"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def board_info() -> None:
    """Stub for test_board_info (port deferred)."""

@test.skip("pending tryke port")
async def system_status_subscription() -> None:
    """Stub for test_system_status_subscription (port deferred)."""
