"""Tryke skip-stubs for myneomitis select tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def select_placeholder() -> None:
    """Placeholder skipped sibling tests for test_select.py."""
