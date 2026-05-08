"""Tryke skip-stubs for mqtt device tracker tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def device_tracker_placeholder() -> None:
    """Placeholder skipped sibling tests for test_device_tracker.py."""
