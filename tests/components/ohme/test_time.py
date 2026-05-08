"""Tryke skip-stubs for ohme time tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def time_placeholder() -> None:
    """Placeholder skipped sibling tests for test_time.py."""
