"""Tryke skip-stubs for nyt_games init tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def init_placeholder() -> None:
    """Placeholder skipped sibling tests for test_init.py."""
