"""Tryke skip-stubs for pglab discovery tests.

Original tests use MQTT discovery + per-platform device registry; full port deferred.
"""

from tryke import test

@test.skip("MQTT discovery + per-platform device registry")
async def device_discover() -> None:
    """Test setting up a device."""

@test.skip("MQTT discovery + per-platform device registry")
async def device_update() -> None:
    """Test update a device."""

@test.skip("MQTT discovery + per-platform device registry")
async def device_remove() -> None:
    """Test remove a device."""
