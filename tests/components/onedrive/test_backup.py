"""Tryke skip-stubs for onedrive backup tests."""

from tryke import test


@test.skip("websocket client tests — needs broader ws shim coverage")
async def backup_placeholder() -> None:
    """Placeholder skipped sibling tests for test_backup.py."""
