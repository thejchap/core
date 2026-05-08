"""Tryke skip-stubs for mqtt image tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def image_placeholder() -> None:
    """Placeholder skipped sibling tests for test_image.py."""
