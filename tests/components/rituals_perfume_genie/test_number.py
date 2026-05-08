"""Tests for the Rituals Perfume Genie number platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def number_entity() -> None:
    """Stub for test_number_entity (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def set_number_value() -> None:
    """Stub for test_set_number_value (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def set_number_value_out_of_range() -> None:
    """Stub for test_set_number_value_out_of_range (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def set_number_value_to_float() -> None:
    """Stub for test_set_number_value_to_float (port deferred)."""
