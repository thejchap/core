"""Tryke skip-stubs for music_assistant init tests."""

from tryke import test


@test.skip("websocket client tests — needs broader ws shim coverage")
async def init_placeholder() -> None:
    """Placeholder skipped sibling tests for test_init.py."""
