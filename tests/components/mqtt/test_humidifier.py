"""Tryke skip-stubs for mqtt humidifier tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def humidifier_placeholder() -> None:
    """Placeholder skipped sibling tests for test_humidifier.py."""
