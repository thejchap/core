"""Tryke skip-stubs for test_event.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def events() -> None:
    """Stub for test_events."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def xiaomi_fingerprint() -> None:
    """Stub for test_xiaomi_fingerprint."""


@test.skip("xiaomi_ble: sibling test pending tryke port")
async def xiaomi_lock() -> None:
    """Stub for test_xiaomi_lock."""
