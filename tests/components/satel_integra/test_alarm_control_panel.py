"""Test Satel Integra alarm panel. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def alarm_control_panel() -> None:
    """Stub for test_alarm_control_panel (port deferred)."""

@test.skip("syrupy snapshot")
async def alarm_control_panel_initial_state() -> None:
    """Stub for test_alarm_control_panel_initial_state (port deferred)."""

@test.skip("syrupy snapshot")
async def alarm_status_callback() -> None:
    """Stub for test_alarm_status_callback (port deferred)."""

@test.skip("syrupy snapshot")
async def alarm_status_callback_debounce() -> None:
    """Stub for test_alarm_status_callback_debounce (port deferred)."""

@test.skip("syrupy snapshot")
async def alarm_control_panel_arming() -> None:
    """Stub for test_alarm_control_panel_arming (port deferred)."""

@test.skip("syrupy snapshot")
async def alarm_control_panel_disarming() -> None:
    """Stub for test_alarm_control_panel_disarming (port deferred)."""

@test.skip("syrupy snapshot")
async def alarm_panel_last_reported() -> None:
    """Stub for test_alarm_panel_last_reported (port deferred)."""

@test.skip("syrupy snapshot")
async def availability() -> None:
    """Stub for test_availability (port deferred)."""
