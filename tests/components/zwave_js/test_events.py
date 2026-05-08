"""Tryke skip-stubs for test_events.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zwave_js: sibling test pending tryke port")
async def scenes() -> None:
    """Stub for test_scenes."""


@test.skip("zwave_js: sibling test pending tryke port")
async def notifications() -> None:
    """Stub for test_notifications."""


@test.skip("zwave_js: sibling test pending tryke port")
async def value_updated() -> None:
    """Stub for test_value_updated."""


@test.skip("zwave_js: sibling test pending tryke port")
async def power_level_notification() -> None:
    """Stub for test_power_level_notification."""


@test.skip("zwave_js: sibling test pending tryke port")
async def unknown_notification() -> None:
    """Stub for test_unknown_notification."""
