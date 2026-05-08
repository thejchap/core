"""Tryke skip-stubs for mqtt diagnostics tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def diagnostics_placeholder() -> None:
    """Placeholder skipped sibling tests for test_diagnostics.py."""
