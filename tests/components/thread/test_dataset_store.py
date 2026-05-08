"""Tryke skip stub for test_dataset_store.py - sibling test pending tryke port."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("thread: sibling test pending tryke port — needs: hass_storage")
async def dataset_store() -> None:
    """Placeholder skipped sibling tests."""
