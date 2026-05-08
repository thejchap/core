"""Tryke skip-stubs for mqtt trigger tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def trigger_placeholder() -> None:
    """Placeholder skipped sibling tests for test_trigger.py."""
