"""Tryke skip-stubs for teslemetry/test_binary_sensor.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def binary_sensor() -> None:
    """Stub for test_binary_sensor."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def binary_sensor_refresh() -> None:
    """Stub for test_binary_sensor_refresh."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def binary_sensors_streaming() -> None:
    """Stub for test_binary_sensors_streaming."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def binary_sensors_connectivity() -> None:
    """Stub for test_binary_sensors_connectivity."""

