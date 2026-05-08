"""Tryke skip-stubs for mqtt light tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def light_placeholder() -> None:
    """Placeholder skipped sibling tests for test_light.py."""
