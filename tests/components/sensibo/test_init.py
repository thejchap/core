"""Test for Sensibo integration setup. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_entry() -> None:
    """Stub for test_migrate_entry (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_entry_fails() -> None:
    """Stub for test_migrate_entry_fails (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def device_remove_devices() -> None:
    """Stub for test_device_remove_devices (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def automatic_device_addition_and_removal() -> None:
    """Stub for test_automatic_device_addition_and_removal (port deferred)."""
