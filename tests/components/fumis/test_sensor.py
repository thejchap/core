"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fumis.sensor module imports cleanly."""
    from homeassistant.components.fumis import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors_disabled_by_default() -> None:
    """Stub for test_sensors_disabled_by_default."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors_unknown_status() -> None:
    """Stub for test_sensors_unknown_status."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors_active_error_and_alert() -> None:
    """Stub for test_sensors_active_error_and_alert."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors_conditional_creation() -> None:
    """Stub for test_sensors_conditional_creation."""

