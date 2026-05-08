"""Tryke skip stub for test_sensor.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the green_planet_energy.sensor module imports cleanly."""
    from homeassistant.components.green_planet_energy import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensors() -> None:
    """Stub for test_sensors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_device_info() -> None:
    """Stub for test_sensor_device_info."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def lowest_price_day_uses_tomorrow_after_18() -> None:
    """Stub for test_lowest_price_day_uses_tomorrow_after_18."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def lowest_price_night_time_uses_upcoming_night_after_06() -> None:
    """Stub for test_lowest_price_night_time_uses_upcoming_night_after_06."""

