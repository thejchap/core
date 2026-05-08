"""Tryke skip-stubs for mqtt device trigger tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def device_trigger_placeholder() -> None:
    """Placeholder skipped sibling tests for test_device_trigger.py."""
