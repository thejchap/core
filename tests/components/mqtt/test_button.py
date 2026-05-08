"""Tryke skip-stubs for mqtt button tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def button_placeholder() -> None:
    """Placeholder skipped sibling tests for test_button.py."""
