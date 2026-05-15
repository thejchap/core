"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_entry() -> None:
    """Stub for test_setup_entry (port deferred)."""

@test.skip("pending tryke port")
async def setup_entry_no_hassio() -> None:
    """Stub for test_setup_entry_no_hassio (port deferred)."""

@test.skip("pending tryke port")
async def setup_entry_wrong_board() -> None:
    """Stub for test_setup_entry_wrong_board (port deferred)."""

@test.skip("pending tryke port")
async def setup_entry_wait_hassio() -> None:
    """Stub for test_setup_entry_wait_hassio (port deferred)."""
