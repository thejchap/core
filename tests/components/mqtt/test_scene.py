"""Tryke skip-stubs for mqtt scene tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def scene_placeholder() -> None:
    """Placeholder skipped sibling tests for test_scene.py."""
