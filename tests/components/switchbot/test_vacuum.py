"""Tests for switchbot vacuum. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def vacuum_controlling() -> None:
    """Stub for test_vacuum_controlling (port deferred)."""
