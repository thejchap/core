"""Test Portainer system health. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def system_health() -> None:
    """Stub for test_system_health (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def system_health_failed_connect() -> None:
    """Stub for test_system_health_failed_connect (port deferred)."""
