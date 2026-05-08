"""Tryke skip-stubs for mqtt climate tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def climate_placeholder() -> None:
    """Placeholder skipped sibling tests for test_climate.py."""
