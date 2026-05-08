"""Tryke skip stub for test_update.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("tplink_omada: sibling test pending tryke port — needs: syrupy snapshot, ws client")
async def update() -> None:
    """Placeholder skipped sibling tests."""
