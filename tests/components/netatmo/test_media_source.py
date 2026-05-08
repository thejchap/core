"""Tryke skip-stubs for netatmo media source tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def media_source_placeholder() -> None:
    """Placeholder skipped sibling tests for test_media_source.py."""
