"""Tryke skip stub for test_diagnostics.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("tplink: sibling test pending tryke port")
async def diagnostics() -> None:
    """Placeholder skipped sibling tests."""
