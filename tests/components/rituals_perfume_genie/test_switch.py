"""Tests for the Rituals Perfume Genie switch platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def switch_entity() -> None:
    """Stub for test_switch_entity (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def switch_handle_coordinator_update() -> None:
    """Stub for test_switch_handle_coordinator_update (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def set_switch_state() -> None:
    """Stub for test_set_switch_state (port deferred)."""
