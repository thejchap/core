"""Tryke skip-stubs for overkiz sensor tests.

Original tests use OverkizClient API mocks + token refresh; full port deferred.
"""

from tryke import test

@test.skip("OverkizClient API mocks + token refresh")
async def sensor_entities_snapshot() -> None:
    """Test representative real setups via snapshot."""

@test.skip("OverkizClient API mocks + token refresh")
async def sensor_temperature_state_update() -> None:
    """Test event-driven state update for a float sensor (temperature 24.4 → 22.1)."""

@test.skip("OverkizClient API mocks + token refresh")
async def sensor_battery_level_state_update() -> None:
    """Test event-driven state update for an integer sensor (battery 59 → 42)."""

@test.skip("OverkizClient API mocks + token refresh")
async def sensor_unavailability() -> None:
    """Test sensor becomes unavailable when device goes offline."""
