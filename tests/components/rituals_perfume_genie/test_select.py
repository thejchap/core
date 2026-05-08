"""Tests for the Rituals Perfume Genie select platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def select_entity() -> None:
    """Stub for test_select_entity (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def select_option() -> None:
    """Stub for test_select_option (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def select_invalid_option() -> None:
    """Stub for test_select_invalid_option (port deferred)."""
