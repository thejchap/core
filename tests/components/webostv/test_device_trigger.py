"""Tryke skip stub for test_device_trigger.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("webostv: sibling test pending tryke port — needs: complex parametrize")
async def device_trigger() -> None:
    """Placeholder skipped sibling tests."""
