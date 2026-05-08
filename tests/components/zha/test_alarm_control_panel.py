"""Tryke skip-stubs for test_alarm_control_panel.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def alarm_control_panel() -> None:
    """Stub for test_alarm_control_panel."""
