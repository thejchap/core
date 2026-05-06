"""Tryke skip stub for test_sensor.py - sibling test pending fixture and snapshot port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("airgradient sibling tests need conftest fixture migration into _fixtures.py and/or syrupy snapshot support")
async def placeholder() -> None:
    """Placeholder skipped sibling tests."""
