"""Tryke skip-stubs for playstation_network notify tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def notify_placeholder() -> None:
    """Placeholder skipped sibling tests for test_notify.py."""
