"""Tests for the switchbot select platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def time_format_select_initial_state() -> None:
    """Stub for test_time_format_select_initial_state (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def set_time_format() -> None:
    """Stub for test_set_time_format (port deferred)."""
