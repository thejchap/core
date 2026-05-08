"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the github.sensor module imports cleanly."""
    from homeassistant.components.github import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_updates_with_empty_release_array() -> None:
    """Stub for test_sensor_updates_with_empty_release_array."""

