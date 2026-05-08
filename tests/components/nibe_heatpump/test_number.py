"""Tryke skip-stubs for nibe_heatpump number tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def number_placeholder() -> None:
    """Placeholder skipped sibling tests for test_number.py."""
