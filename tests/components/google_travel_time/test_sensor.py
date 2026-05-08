"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_travel_time.sensor module imports cleanly."""
    from homeassistant.components.google_travel_time import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_empty_response() -> None:
    """Stub for test_sensor_empty_response."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_departure_time() -> None:
    """Stub for test_sensor_departure_time."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_arrival_time() -> None:
    """Stub for test_sensor_arrival_time."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_unit_system() -> None:
    """Stub for test_sensor_unit_system."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_exception() -> None:
    """Stub for test_sensor_exception."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_routes_api_disabled() -> None:
    """Stub for test_sensor_routes_api_disabled."""

