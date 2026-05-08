"""Tryke skip-stubs for mqtt switch tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def switch_placeholder() -> None:
    """Placeholder skipped sibling tests for test_switch.py."""
