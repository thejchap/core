"""Test smarttub setup process. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_with_no_config() -> None:
    """Stub for test_setup_with_no_config (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_entry_not_ready() -> None:
    """Stub for test_setup_entry_not_ready (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_auth_failed() -> None:
    """Stub for test_setup_auth_failed (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry (port deferred)."""
