"""Tryke skip-stubs for mqtt vacuum tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def vacuum_placeholder() -> None:
    """Placeholder skipped sibling tests for test_vacuum.py."""
