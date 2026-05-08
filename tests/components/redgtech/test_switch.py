"""Tests for the Redgtech switch platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("syrupy snapshot")
async def entities() -> None:
    """Stub for test_entities (port deferred)."""

@test.skip("syrupy snapshot")
async def switch_turn_on() -> None:
    """Stub for test_switch_turn_on (port deferred)."""

@test.skip("syrupy snapshot")
async def switch_turn_off() -> None:
    """Stub for test_switch_turn_off (port deferred)."""

@test.skip("syrupy snapshot")
async def switch_toggle() -> None:
    """Stub for test_switch_toggle (port deferred)."""

@test.skip("syrupy snapshot")
async def exception_handling() -> None:
    """Stub for test_exception_handling (port deferred)."""

@test.skip("syrupy snapshot")
async def switch_auth_error_with_retry() -> None:
    """Stub for test_switch_auth_error_with_retry (port deferred)."""

@test.skip("syrupy snapshot")
async def coordinator_data_update_success() -> None:
    """Stub for test_coordinator_data_update_success (port deferred)."""

@test.skip("syrupy snapshot")
async def coordinator_connection_error_during_update() -> None:
    """Stub for test_coordinator_connection_error_during_update (port deferred)."""

@test.skip("syrupy snapshot")
async def coordinator_auth_error_with_token_renewal() -> None:
    """Stub for test_coordinator_auth_error_with_token_renewal (port deferred)."""
