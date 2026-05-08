"""Tryke skip-stubs for test_select.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def select() -> None:
    """Stub for test_select."""


@test.skip("zha: sibling test pending tryke port")
async def select_restore_state() -> None:
    """Stub for test_select_restore_state."""
