"""Tryke skip-stubs for mqtt notify tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def notify_placeholder() -> None:
    """Placeholder skipped sibling tests for test_notify.py."""
