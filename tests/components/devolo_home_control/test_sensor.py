"""Tryke skip stub for test_sensor.py: uses syrupy snapshot — needs pytest --snapshot-update first."""

from tryke import test


@test.skip("snapshot test — out of scope")
async def brightness_sensor() -> None:
    """Stub for test_brightness_sensor."""


@test.skip("snapshot test — out of scope")
async def temperature_sensor() -> None:
    """Stub for test_temperature_sensor."""


@test.skip("snapshot test — out of scope")
async def battery_sensor() -> None:
    """Stub for test_battery_sensor."""


@test.skip("snapshot test — out of scope")
async def consumption_sensor() -> None:
    """Stub for test_consumption_sensor."""


@test.skip("snapshot test — out of scope")
async def voltage_sensor() -> None:
    """Stub for test_voltage_sensor."""


@test.skip("snapshot test — out of scope")
async def sensor_change() -> None:
    """Stub for test_sensor_change."""


@test.skip("snapshot test — out of scope")
async def remove_from_hass() -> None:
    """Stub for test_remove_from_hass."""


