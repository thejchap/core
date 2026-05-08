"""Tests for the Risco integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def connection_reset() -> None:
    """Stub for test_connection_reset (port deferred)."""
