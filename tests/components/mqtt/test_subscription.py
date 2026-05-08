"""Tryke skip-stubs for mqtt subscription tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def subscription_placeholder() -> None:
    """Placeholder skipped sibling tests for test_subscription.py."""
