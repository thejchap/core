"""Tryke skip-stubs for mqtt time tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def time_placeholder() -> None:
    """Placeholder skipped sibling tests for test_time.py."""
