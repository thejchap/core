"""Tryke skip stubs for test_sensor - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sensor_platform() -> None:
    """Stub for test_sensor_platform (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def entity_not_created_when_key_missing() -> None:
    """Stub for test_entity_not_created_when_key_missing (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def wifi_rssi_disabled_by_default() -> None:
    """Stub for test_wifi_rssi_disabled_by_default (port deferred)."""


