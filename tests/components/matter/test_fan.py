"""Tryke skip-stubs for matter fan tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def fan_placeholder() -> None:
    """Placeholder skipped sibling tests for test_fan.py."""
