"""Tryke skip-stubs for mysensors test_sensor (port deferred)."""
from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.mysensors.sensor module imports cleanly."""
    from homeassistant.components.mysensors import sensor  # noqa: PLC0415
    expect(sensor).not_.to_be(None)


@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def gps_sensor() -> None:
    """Stub for test_gps_sensor (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def ir_transceiver() -> None:
    """Stub for test_ir_transceiver (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def battery_entity() -> None:
    """Stub for test_battery_entity (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def power_sensor() -> None:
    """Stub for test_power_sensor (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def energy_sensor() -> None:
    """Stub for test_energy_sensor (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def sound_sensor() -> None:
    """Stub for test_sound_sensor (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def distance_sensor() -> None:
    """Stub for test_distance_sensor (port deferred)."""

@test.skip("requires mysensors gateway socket+serial fixtures (not in tryke shim)")
async def temperature_sensor() -> None:
    """Stub for test_temperature_sensor (port deferred)."""


