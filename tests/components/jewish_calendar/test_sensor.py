"""Tryke skip-stubs for test_sensor.py - indirect parametrize unsupported."""

from tryke import test

@test.skip("indirect parametrize unsupported")
async def min_config() -> None:
    """Stub for test_min_config."""

@test.skip("indirect parametrize unsupported")
async def jewish_calendar_sensor() -> None:
    """Stub for test_jewish_calendar_sensor."""

@test.skip("indirect parametrize unsupported")
async def shabbat_times_sensor() -> None:
    """Stub for test_shabbat_times_sensor."""

@test.skip("indirect parametrize unsupported")
async def omer_sensor() -> None:
    """Stub for test_omer_sensor."""

@test.skip("indirect parametrize unsupported")
async def dafyomi_sensor() -> None:
    """Stub for test_dafyomi_sensor."""

@test.skip("indirect parametrize unsupported")
async def sensor_date_changes_with_time() -> None:
    """Stub for test_sensor_date_changes_with_time."""
