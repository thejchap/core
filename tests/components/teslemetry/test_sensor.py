"""Tryke skip-stubs for teslemetry/test_sensor.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def sensors() -> None:
    """Stub for test_sensors."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def sensors_streaming() -> None:
    """Stub for test_sensors_streaming."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def energy_history_no_time_series() -> None:
    """Stub for test_energy_history_no_time_series."""

