"""Tryke skip-stubs for mqtt event tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def event_placeholder() -> None:
    """Placeholder skipped sibling tests for test_event.py."""
