"""Tests for the srp_energy sensor platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def loading_sensors() -> None:
    """Stub for test_loading_sensors (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def srp_entity() -> None:
    """Stub for test_srp_entity (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def srp_entity_update_failed() -> None:
    """Stub for test_srp_entity_update_failed (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def srp_entity_timeout() -> None:
    """Stub for test_srp_entity_timeout (port deferred)."""
