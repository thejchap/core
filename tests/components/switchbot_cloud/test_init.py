"""Tests for the SwitchBot Cloud integration init. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_entry_success() -> None:
    """Stub for test_setup_entry_success (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_entry_fails_when_listing_devices() -> None:
    """Stub for test_setup_entry_fails_when_listing_devices (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_entry_fails_when_refreshing() -> None:
    """Stub for test_setup_entry_fails_when_refreshing (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def posting_to_webhook() -> None:
    """Stub for test_posting_to_webhook (port deferred)."""
