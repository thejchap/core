"""Tryke skip stub for test_alarm_control_panel.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("tuya: sibling test pending tryke port — needs: syrupy snapshot")
async def alarm_control_panel() -> None:
    """Placeholder skipped sibling tests."""
