"""Tryke skip-stubs for powerwall sensor tests.

Original tests use Powerwall API mocks; full port deferred.
"""

from tryke import test

@test.skip("Powerwall API mocks")
async def sensors() -> None:
    """Test creation of the sensors."""

@test.skip("Powerwall API mocks")
async def sensor_backup_reserve_unavailable() -> None:
    """Confirm that backup reserve sensor is not added if data is unavailable from the device."""

@test.skip("Powerwall API mocks")
async def sensors_with_empty_meters() -> None:
    """Test creation of the sensors with empty meters."""

@test.skip("Powerwall API mocks")
async def unique_id_migrate() -> None:
    """Test we can migrate unique ids of the sensors."""
