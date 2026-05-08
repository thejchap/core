"""Tryke skip-stubs for music_assistant media browser tests."""

from tryke import test


@test.skip("sibling test port deferred — depends on conftest fixtures not yet migrated to _fixtures.py")
async def media_browser_placeholder() -> None:
    """Placeholder skipped sibling tests for test_media_browser.py."""
