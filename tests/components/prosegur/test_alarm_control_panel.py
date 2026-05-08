"""Tests for the Prosegur alarm control panel device. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def entity_registry() -> None:
    """Stub for test_entity_registry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def connection_error() -> None:
    """Stub for test_connection_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def arm() -> None:
    """Stub for test_arm (port deferred)."""
