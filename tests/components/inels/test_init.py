"""Tryke skip-stubs for test_init.py - mqtt_mock not in shim."""

from tryke import test

@test.skip("mqtt_mock not in shim")
async def ha_mqtt_publish() -> None:
    """Stub for test_ha_mqtt_publish."""

@test.skip("mqtt_mock not in shim")
async def ha_mqtt_subscribe() -> None:
    """Stub for test_ha_mqtt_subscribe."""

@test.skip("mqtt_mock not in shim")
async def ha_mqtt_not_available() -> None:
    """Stub for test_ha_mqtt_not_available."""

@test.skip("mqtt_mock not in shim")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""
