"""Tryke skip-stubs for test_binary_sensor.py - indirect parametrize unsupported."""

from tryke import test

@test.skip("indirect parametrize unsupported")
async def paired_depaired_devices_flow() -> None:
    """Stub for test_paired_depaired_devices_flow."""

@test.skip("indirect parametrize unsupported")
async def connected_devices() -> None:
    """Stub for test_connected_devices."""

@test.skip("indirect parametrize unsupported")
async def binary_sensors_entity_availability() -> None:
    """Stub for test_binary_sensors_entity_availability."""

@test.skip("indirect parametrize unsupported")
async def binary_sensors_functionality() -> None:
    """Stub for test_binary_sensors_functionality."""

@test.skip("indirect parametrize unsupported")
async def connected_sensor_functionality() -> None:
    """Stub for test_connected_sensor_functionality."""
