"""Tryke skip-stubs for mqtt text tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def text_placeholder() -> None:
    """Placeholder skipped sibling tests for test_text.py."""
