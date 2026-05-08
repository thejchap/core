"""Tests for the Risco event sensors. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def error_on_login() -> None:
    """Stub for test_error_on_login (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def cloud_setup() -> None:
    """Stub for test_cloud_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def local_setup() -> None:
    """Stub for test_local_setup (port deferred)."""
