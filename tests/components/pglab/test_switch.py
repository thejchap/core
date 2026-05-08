"""Tryke skip-stubs for pglab switch tests.

Original tests use MQTT discovery + per-platform device registry; full port deferred.
"""

from tryke import test

@test.skip("MQTT discovery + per-platform device registry")
async def available_relay() -> None:
    """Check if relay are properly created when two E-Relay boards are connected."""

@test.skip("MQTT discovery + per-platform device registry")
async def change_state_via_mqtt() -> None:
    """Test state update via MQTT."""

@test.skip("MQTT discovery + per-platform device registry")
async def mqtt_state_by_calling_service() -> None:
    """Calling service to turn ON/OFF relay and check mqtt state."""

@test.skip("MQTT discovery + per-platform device registry")
async def discovery_update() -> None:
    """Update discovery message and  check if relay are property updated."""

@test.skip("MQTT discovery + per-platform device registry")
async def disable_entity_state_change_via_mqtt() -> None:
    """Test state update via MQTT of disable entity."""
