"""Tryke skip-stubs for peblar update tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def update_placeholder() -> None:
    """Placeholder skipped sibling tests for test_update.py."""
