"""Tryke skip-stubs for pglab cover tests.

Original tests use MQTT discovery + per-platform device registry; full port deferred.
"""

from tryke import test

@test.skip("MQTT discovery + per-platform device registry")
async def cover_features() -> None:
    """Test cover features."""

@test.skip("MQTT discovery + per-platform device registry")
async def cover_availability() -> None:
    """Check if covers are properly created."""

@test.skip("MQTT discovery + per-platform device registry")
async def cover_change_state_via_mqtt() -> None:
    """Test state update via MQTT."""

@test.skip("MQTT discovery + per-platform device registry")
async def cover_mqtt_state_by_calling_service() -> None:
    """Calling service to OPEN/CLOSE cover and check mqtt state."""
