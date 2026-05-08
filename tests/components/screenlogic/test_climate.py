"""Tests for ScreenLogic climate entity. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def climate_state() -> None:
    """Stub for test_climate_state (port deferred)."""
