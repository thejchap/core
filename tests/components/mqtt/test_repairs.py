"""Tryke skip-stubs for mqtt repairs tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def repairs_placeholder() -> None:
    """Placeholder skipped sibling tests for test_repairs.py."""
