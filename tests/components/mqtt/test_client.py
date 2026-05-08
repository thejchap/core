"""Tryke skip-stubs for mqtt client tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def client_placeholder() -> None:
    """Placeholder skipped sibling tests for test_client.py."""
