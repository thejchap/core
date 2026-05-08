"""Tryke skip-stubs for mqtt siren tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def siren_placeholder() -> None:
    """Placeholder skipped sibling tests for test_siren.py."""
