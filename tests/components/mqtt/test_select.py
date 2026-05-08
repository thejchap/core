"""Tryke skip-stubs for mqtt select tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def select_placeholder() -> None:
    """Placeholder skipped sibling tests for test_select.py."""
