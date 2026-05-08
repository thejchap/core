"""Tryke skip-stubs for test_alarm_control_panel.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yale_smart_alarm: needs load_config_entry / get_client conftest fixtures")
async def alarm_control_panel() -> None:
    """Stub for test_alarm_control_panel."""


@test.skip("yale_smart_alarm: needs load_config_entry / get_client conftest fixtures")
async def alarm_control_panel_service_calls() -> None:
    """Stub for test_alarm_control_panel_service_calls."""


@test.skip("yale_smart_alarm: needs load_config_entry / get_client conftest fixtures")
async def alarm_control_panel_not_available() -> None:
    """Stub for test_alarm_control_panel_not_available."""
