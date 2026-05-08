"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the freshr.sensor module imports cleanly."""
    from homeassistant.components.freshr import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entities() -> None:
    """Stub for test_entities."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_none_values() -> None:
    """Stub for test_sensor_none_values."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def readings_connection_error_makes_unavailable() -> None:
    """Stub for test_readings_connection_error_makes_unavailable."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_reappears_after_removal() -> None:
    """Stub for test_device_reappears_after_removal."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def dynamic_device_added() -> None:
    """Stub for test_dynamic_device_added."""

