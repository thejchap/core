"""Tryke skip stub for test_binary_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fumis.binary_sensor module imports cleanly."""
    from homeassistant.components.fumis import binary_sensor  # noqa: PLC0415
    expect(binary_sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def binary_sensors() -> None:
    """Stub for test_binary_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def binary_sensors_conditional_creation() -> None:
    """Stub for test_binary_sensors_conditional_creation."""

