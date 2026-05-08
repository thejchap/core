"""Tryke skip-stubs for plugwise button tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def button_placeholder() -> None:
    """Placeholder skipped sibling tests for test_button.py."""
