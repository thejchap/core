"""Tryke skip-stubs for music_assistant text tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def text_placeholder() -> None:
    """Placeholder skipped sibling tests for test_text.py."""
