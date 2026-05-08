"""Tests for the binary sensor platform of the Pterodactyl integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def binary_sensor() -> None:
    """Stub for test_binary_sensor (port deferred)."""

@test.skip("syrupy snapshot")
async def binary_sensor_update() -> None:
    """Stub for test_binary_sensor_update (port deferred)."""

@test.skip("syrupy snapshot")
async def binary_sensor_update_failure() -> None:
    """Stub for test_binary_sensor_update_failure (port deferred)."""
