"""Tryke skip-stubs for lojack device tracker tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def device_tracker_placeholder() -> None:
    """Placeholder skipped sibling tests for test_device_tracker.py."""
