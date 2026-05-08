"""Tryke skip-stubs for myuplink sensor tests."""

from tryke import test


@test.skip("snapshot-based test — needs pytest --snapshot-update to regenerate before tryke can run read-only")
async def sensor_placeholder() -> None:
    """Placeholder skipped sibling tests for test_sensor.py."""
