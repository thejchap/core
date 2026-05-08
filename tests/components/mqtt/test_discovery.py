"""Tryke skip-stubs for mqtt discovery tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def discovery_placeholder() -> None:
    """Placeholder skipped sibling tests for test_discovery.py."""
