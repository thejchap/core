"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the google_weather.sensor module imports cleanly."""
    from homeassistant.components.google_weather import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor() -> None:
    """Stub for test_sensor."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def availability() -> None:
    """Stub for test_availability."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def manual_update_entity() -> None:
    """Stub for test_manual_update_entity."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_imperial_units() -> None:
    """Stub for test_sensor_imperial_units."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_update() -> None:
    """Stub for test_state_update."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def auth_failure_during_update() -> None:
    """Stub for test_auth_failure_during_update."""

