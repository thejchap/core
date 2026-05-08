"""Tryke skip-stubs for nest test_sensor (port deferred)."""
from tryke import test

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def temperature_rounding() -> None:
    """Stub for test_temperature_rounding (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def thermostat_device() -> None:
    """Stub for test_thermostat_device (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def thermostat_device_available() -> None:
    """Stub for test_thermostat_device_available (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def thermostat_device_unavailable() -> None:
    """Stub for test_thermostat_device_unavailable (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def no_devices() -> None:
    """Stub for test_no_devices (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def device_no_sensor_traits() -> None:
    """Stub for test_device_no_sensor_traits (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def device_name_from_structure() -> None:
    """Stub for test_device_name_from_structure (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def event_updates_sensor() -> None:
    """Stub for test_event_updates_sensor (port deferred)."""

@test.skip("OAuth2 application credentials flow / SDM API mocks (not in tryke shim)")
async def device_with_unknown_type() -> None:
    """Stub for test_device_with_unknown_type (port deferred)."""


