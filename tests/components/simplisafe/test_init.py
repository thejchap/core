"""Define tests for SimpliSafe setup. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def base_station_migration() -> None:
    """Stub for test_base_station_migration (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def coordinator_update_triggers_reauth_on_invalid_credentials() -> None:
    """Stub for test_coordinator_update_triggers_reauth_on_invalid_credentials (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def coordinator_update_failure_keeps_entity_available() -> None:
    """Stub for test_coordinator_update_failure_keeps_entity_available (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def websocket_event_updates_entity_state() -> None:
    """Stub for test_websocket_event_updates_entity_state (port deferred)."""
