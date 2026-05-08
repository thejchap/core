"""Tryke skip-stubs for miele vacuum tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def vacuum_placeholder() -> None:
    """Placeholder skipped sibling tests for test_vacuum.py."""
