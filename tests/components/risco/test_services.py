"""Tests for the Risco services. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def set_time_service() -> None:
    """Stub for test_set_time_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def set_time_service_with_no_time() -> None:
    """Stub for test_set_time_service_with_no_time (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def set_time_service_with_invalid_entry() -> None:
    """Stub for test_set_time_service_with_invalid_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def set_time_service_with_not_loaded_entry() -> None:
    """Stub for test_set_time_service_with_not_loaded_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def set_time_service_with_cloud_entry() -> None:
    """Stub for test_set_time_service_with_cloud_entry (port deferred)."""
