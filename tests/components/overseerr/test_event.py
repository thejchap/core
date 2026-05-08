"""Tryke skip-stubs for overseerr event tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def event_placeholder() -> None:
    """Placeholder skipped sibling tests for test_event.py."""
