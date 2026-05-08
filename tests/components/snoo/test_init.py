"""Test init for Snoo. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def cannot_auth() -> None:
    """Stub for test_cannot_auth (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def failed_devices() -> None:
    """Stub for test_failed_devices (port deferred)."""
