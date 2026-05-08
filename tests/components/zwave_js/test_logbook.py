"""Tryke skip-stubs for test_logbook.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def humanifying_zwave_js_notification_event() -> None:
    """Stub for test_humanifying_zwave_js_notification_event."""


@test.skip("zwave_js: sibling test pending tryke port")
async def humanifying_zwave_js_value_notification_event() -> None:
    """Stub for test_humanifying_zwave_js_value_notification_event."""
