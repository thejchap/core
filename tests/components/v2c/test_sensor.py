"""Tryke skip stub for test_sensor.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("v2c: sibling test pending tryke port — needs: syrupy snapshot")
async def sensor() -> None:
    """Placeholder skipped sibling tests."""
