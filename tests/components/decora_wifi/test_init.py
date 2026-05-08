"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_unload_entry() -> None:
    """Stub for test_setup_unload_entry."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_auth_failed() -> None:
    """Stub for test_setup_entry_auth_failed."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_entry_cannot_connect() -> None:
    """Stub for test_setup_entry_cannot_connect."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def unload_entry_logout_failure() -> None:
    """Stub for test_unload_entry_logout_failure."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def stop_event_logs_out() -> None:
    """Stub for test_stop_event_logs_out."""

