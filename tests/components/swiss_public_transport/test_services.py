"""Test the swiss_public_transport service. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def service_call_fetch_connections_success() -> None:
    """Stub for test_service_call_fetch_connections_success (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def service_call_fetch_connections_error() -> None:
    """Stub for test_service_call_fetch_connections_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def service_call_load_unload() -> None:
    """Stub for test_service_call_load_unload (port deferred)."""
