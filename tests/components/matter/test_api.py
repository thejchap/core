"""Tryke skip-stubs for matter api tests."""

from tryke import test


@test.skip("websocket client tests — needs broader ws shim coverage")
async def api_placeholder() -> None:
    """Placeholder skipped sibling tests for test_api.py."""
