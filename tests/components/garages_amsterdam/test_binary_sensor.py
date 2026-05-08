"""Tryke skip stub for test_binary_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the garages_amsterdam.binary_sensor module imports cleanly."""
    from homeassistant.components.garages_amsterdam import binary_sensor  # noqa: PLC0415
    expect(binary_sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def all_binary_sensors() -> None:
    """Stub for test_all_binary_sensors."""

