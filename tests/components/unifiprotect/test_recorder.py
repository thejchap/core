"""Tryke skip stub for test_recorder.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("unifiprotect: sibling test pending tryke port")
async def recorder() -> None:
    """Placeholder skipped sibling tests."""
