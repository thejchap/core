"""Tryke skip-stubs for mqtt util tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def util_placeholder() -> None:
    """Placeholder skipped sibling tests for test_util.py."""
