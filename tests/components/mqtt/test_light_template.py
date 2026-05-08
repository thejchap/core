"""Tryke skip-stubs for mqtt light template tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def light_template_placeholder() -> None:
    """Placeholder skipped sibling tests for test_light_template.py."""
