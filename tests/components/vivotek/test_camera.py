"""Tryke skip stub for test_camera.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("vivotek: sibling test pending tryke port — needs: syrupy snapshot")
async def camera() -> None:
    """Placeholder skipped sibling tests."""
