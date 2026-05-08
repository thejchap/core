"""Tryke skip-stubs for mqtt number tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def number_placeholder() -> None:
    """Placeholder skipped sibling tests for test_number.py."""
