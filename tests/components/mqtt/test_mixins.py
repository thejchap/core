"""Tryke skip-stubs for mqtt mixins tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def mixins_placeholder() -> None:
    """Placeholder skipped sibling tests for test_mixins.py."""
