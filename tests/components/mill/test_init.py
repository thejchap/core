"""Tryke skip-stubs for mill init tests."""

from tryke import test


@test.skip("recorder_mock — needs setup_recorder_mock helper integration")
async def init_placeholder() -> None:
    """Placeholder skipped sibling tests for test_init.py."""
