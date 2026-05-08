"""Tryke skip-stubs for mqtt datetime tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def datetime_placeholder() -> None:
    """Placeholder skipped sibling tests for test_datetime.py."""
