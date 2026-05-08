"""Tryke skip-stubs for ntfy test_diagnostics (port deferred)."""
from tryke import test

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def diagnostics_redacted_url() -> None:
    """Stub for test_diagnostics_redacted_url (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def diagnostics() -> None:
    """Stub for test_diagnostics (port deferred)."""


