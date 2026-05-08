"""Test switch platform for Swing2Sleep Smarla integration. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def init_exception() -> None:
    """Stub for test_init_exception (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def init_auth_failure_during_runtime() -> None:
    """Stub for test_init_auth_failure_during_runtime (port deferred)."""
