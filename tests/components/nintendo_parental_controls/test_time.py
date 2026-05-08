"""Tryke skip-stubs for nintendo_parental_controls time tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def time_placeholder() -> None:
    """Placeholder skipped sibling tests for test_time.py."""
