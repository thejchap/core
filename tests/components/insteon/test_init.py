"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_entry() -> None:
    """Stub for test_setup_entry (port deferred)."""

@test.skip("pending tryke port")
async def setup_entry_failed_connection() -> None:
    """Stub for test_setup_entry_failed_connection (port deferred)."""

@test.skip("pending tryke port")
async def import_frontend_dev_url() -> None:
    """Stub for test_import_frontend_dev_url (port deferred)."""
