"""Tryke skip-stubs for mqtt alarm control panel tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def alarm_control_panel_placeholder() -> None:
    """Placeholder skipped sibling tests for test_alarm_control_panel.py."""
