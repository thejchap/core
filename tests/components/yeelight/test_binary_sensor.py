"""Tryke skip-stubs for test_binary_sensor.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("yeelight: sibling test pending tryke port")
async def nightlight() -> None:
    """Stub for test_nightlight."""
