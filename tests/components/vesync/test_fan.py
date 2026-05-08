"""Tryke skip stub for test_fan.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("vesync: sibling test pending tryke port — needs: syrupy snapshot, aioclient_mock")
async def fan() -> None:
    """Placeholder skipped sibling tests."""
