"""Tests for the Sonos statistics. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def statistics_duplicate() -> None:
    """Stub for test_statistics_duplicate (port deferred)."""
