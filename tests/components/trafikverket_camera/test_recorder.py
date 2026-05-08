"""Tryke skip stub for test_recorder.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("trafikverket_camera: sibling test pending tryke port — needs: recorder_mock, aioclient_mock")
async def recorder() -> None:
    """Placeholder skipped sibling tests."""
