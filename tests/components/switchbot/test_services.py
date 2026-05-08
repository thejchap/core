"""Test the switchbot services. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def add_password_service() -> None:
    """Stub for test_add_password_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def device_not_found() -> None:
    """Stub for test_device_not_found (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def device_not_belonging() -> None:
    """Stub for test_device_not_belonging (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def device_entry_not_loaded() -> None:
    """Stub for test_device_entry_not_loaded (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def service_unsupported_device() -> None:
    """Stub for test_service_unsupported_device (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def device_without_config_entry_id() -> None:
    """Stub for test_device_without_config_entry_id (port deferred)."""
