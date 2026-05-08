"""Test sensor platform for Swing2Sleep Smarla integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def entities() -> None:
    """Stub for test_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def sensor_state_update() -> None:
    """Stub for test_sensor_state_update (port deferred)."""
