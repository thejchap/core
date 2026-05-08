"""Test Smarla entities. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def entity_availability() -> None:
    """Stub for test_entity_availability (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def entity_unavailable_logging() -> None:
    """Stub for test_entity_unavailable_logging (port deferred)."""
