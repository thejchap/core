"""Tryke skip-stubs for test_fan.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("xiaomi_miio: sibling test pending tryke port")
async def fan_status() -> None:
    """Stub for test_fan_status."""
