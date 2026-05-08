"""Tryke skip-stubs for ntfy test_init (port deferred)."""
from tryke import test

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def coordinator_update_exceptions() -> None:
    """Stub for test_coordinator_update_exceptions (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def entry_setup_unload() -> None:
    """Stub for test_entry_setup_unload (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def config_entry_not_ready() -> None:
    """Stub for test_config_entry_not_ready (port deferred)."""


