"""Tryke skip-stubs for mill coordinator tests."""

from tryke import test


@test.skip("recorder_mock — needs setup_recorder_mock helper integration")
async def coordinator_placeholder() -> None:
    """Placeholder skipped sibling tests for test_coordinator.py."""
