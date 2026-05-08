"""Tryke skip-stubs for palazzetti diagnostics tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def diagnostics_placeholder() -> None:
    """Placeholder skipped sibling tests for test_diagnostics.py."""
