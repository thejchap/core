"""Tryke skip-stubs for mealie services tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def services_placeholder() -> None:
    """Placeholder skipped sibling tests for test_services.py."""
