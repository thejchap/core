"""Test the Saunum sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def entities() -> None:
    """Stub for test_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def sensor_not_created_when_value_is_none() -> None:
    """Stub for test_sensor_not_created_when_value_is_none (port deferred)."""

@test.skip("syrupy snapshot")
async def entity_unavailable_on_update_failure() -> None:
    """Stub for test_entity_unavailable_on_update_failure (port deferred)."""
