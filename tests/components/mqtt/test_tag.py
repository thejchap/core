"""Tryke skip-stubs for mqtt tag tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def tag_placeholder() -> None:
    """Placeholder skipped sibling tests for test_tag.py."""
