"""Tryke skip stub for test_sensor.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("touchline_sl: sibling test pending tryke port — needs: complex parametrize")
async def sensor() -> None:
    """Placeholder skipped sibling tests."""
