"""Tryke skip-stubs for tesla_fleet/test_binary_sensor.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def binary_sensor() -> None:
    """Stub for test_binary_sensor."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def binary_sensor_refresh() -> None:
    """Stub for test_binary_sensor_refresh."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def binary_sensor_offline() -> None:
    """Stub for test_binary_sensor_offline."""

