"""Tryke skip-stubs for mqtt init tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def init_placeholder() -> None:
    """Placeholder skipped sibling tests for test_init.py."""
