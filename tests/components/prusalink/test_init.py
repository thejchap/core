"""Test setting up and unloading PrusaLink. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def device_info() -> None:
    """Stub for test_device_info (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def unloading() -> None:
    """Stub for test_unloading (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def failed_update() -> None:
    """Stub for test_failed_update (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migration_from_1_1_to_1_2() -> None:
    """Stub for test_migration_from_1_1_to_1_2 (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migration_from_1_1_to_1_2_outdated_firmware() -> None:
    """Stub for test_migration_from_1_1_to_1_2_outdated_firmware (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migration_fails_on_future_version() -> None:
    """Stub for test_migration_fails_on_future_version (port deferred)."""
