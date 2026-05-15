"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def button() -> None:
    """Stub for test_button (port deferred)."""

@test.skip("pending tryke port")
async def ptz_move_service() -> None:
    """Stub for test_ptz_move_service (port deferred)."""

@test.skip("pending tryke port")
async def host_button() -> None:
    """Stub for test_host_button (port deferred)."""
