"""Tryke skip-stubs for mqtt light json tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def light_json_placeholder() -> None:
    """Placeholder skipped sibling tests for test_light_json.py."""
