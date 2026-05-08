"""Tryke skip stub for test_camera.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("trafikverket_camera: sibling test pending tryke port — needs: aioclient_mock")
async def camera() -> None:
    """Placeholder skipped sibling tests."""
