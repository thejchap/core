"""Tryke skip-stubs for nice_go light tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def light_placeholder() -> None:
    """Placeholder skipped sibling tests for test_light.py."""
