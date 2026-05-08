"""Tryke skip-stubs for test_logbook.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("zha: sibling test pending tryke port")
async def zha_logbook_event_device_with_triggers() -> None:
    """Stub for test_zha_logbook_event_device_with_triggers."""


@test.skip("zha: sibling test pending tryke port")
async def zha_logbook_event_device_no_triggers() -> None:
    """Stub for test_zha_logbook_event_device_no_triggers."""


@test.skip("zha: sibling test pending tryke port")
async def zha_logbook_event_device_no_device() -> None:
    """Stub for test_zha_logbook_event_device_no_device."""
