"""Tryke skip-stubs for tasmota/test_init.py."""

from tryke import test


@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def device_remove() -> None:
    """Stub for test_device_remove."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def device_remove_non_tasmota_device() -> None:
    """Stub for test_device_remove_non_tasmota_device."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def device_remove_stale_tasmota_device() -> None:
    """Stub for test_device_remove_stale_tasmota_device."""

@test.skip("requires mqtt_mock + tasmota discovery — port deferred")
async def tasmota_ws_remove_discovered_device() -> None:
    """Stub for test_tasmota_ws_remove_discovered_device."""

