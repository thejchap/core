"""Tryke skip-stubs for mqtt camera tests."""

from tryke import test


@test.skip("mqtt_mock fixture not in tryke shim")
async def camera_placeholder() -> None:
    """Placeholder skipped sibling tests for test_camera.py."""
