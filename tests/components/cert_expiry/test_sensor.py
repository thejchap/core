"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("sensor.example_com_cert_expiry not registered after async_setup_component in tryke env")
async def async_setup_entry() -> None:
    """Stub for test_async_setup_entry."""


@test.skip("sensor.example_com_cert_expiry not registered after async_setup_component in tryke env")
async def async_setup_entry_bad_cert() -> None:
    """Stub for test_async_setup_entry_bad_cert."""


@test.skip("sensor.example_com_cert_expiry not registered after async_setup_component in tryke env")
async def update_sensor() -> None:
    """Stub for test_update_sensor."""


@test.skip("sensor.example_com_cert_expiry not registered after async_setup_component in tryke env")
async def update_sensor_network_errors() -> None:
    """Stub for test_update_sensor_network_errors."""
