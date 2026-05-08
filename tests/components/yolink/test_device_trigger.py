"""Tryke skip-stubs for test_device_trigger.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yolink: sibling test pending tryke port")
async def get_triggers() -> None:
    """Stub for test_get_triggers."""


@test.skip("yolink: sibling test pending tryke port")
async def get_triggers_exception() -> None:
    """Stub for test_get_triggers_exception."""


@test.skip("yolink: sibling test pending tryke port")
async def if_fires_on_event() -> None:
    """Stub for test_if_fires_on_event."""
