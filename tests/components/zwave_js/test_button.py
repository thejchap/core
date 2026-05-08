"""Tryke skip-stubs for test_button.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def ping_entity() -> None:
    """Stub for test_ping_entity."""


@test.skip("zwave_js: sibling test pending tryke port")
async def notification_idle_button() -> None:
    """Stub for test_notification_idle_button."""
