"""Tryke skip-stubs for mqtt lawn mower tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def lawn_mower_placeholder() -> None:
    """Placeholder skipped sibling tests for test_lawn_mower.py."""
