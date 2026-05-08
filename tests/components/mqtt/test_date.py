"""Tryke skip-stubs for mqtt date tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def date_placeholder() -> None:
    """Placeholder skipped sibling tests for test_date.py."""
