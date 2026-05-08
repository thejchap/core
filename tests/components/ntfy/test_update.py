"""Tryke skip-stubs for ntfy test_update (port deferred)."""
from tryke import test

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def with_official_server() -> None:
    """Stub for test_with_official_server (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def update_checker_error() -> None:
    """Stub for test_update_checker_error (port deferred)."""

@test.skip("requires aiontfy + Notification/Account/Event mocks (not ported)")
async def version_errors() -> None:
    """Stub for test_version_errors (port deferred)."""


