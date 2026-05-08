"""Test the sma init file. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def migrate_entry_minor_version_1_2() -> None:
    """Stub for test_migrate_entry_minor_version_1_2 (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_exceptions() -> None:
    """Stub for test_setup_exceptions (port deferred)."""
