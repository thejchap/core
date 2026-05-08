"""Tryke skip-stubs for mqtt cover tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def cover_placeholder() -> None:
    """Placeholder skipped sibling tests for test_cover.py."""
