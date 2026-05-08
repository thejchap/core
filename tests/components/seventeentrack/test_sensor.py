"""Tests for the seventeentrack sensor. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def full_valid_config() -> None:
    """Stub for test_full_valid_config (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def valid_config() -> None:
    """Stub for test_valid_config (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def invalid_config() -> None:
    """Stub for test_invalid_config (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def login_exception() -> None:
    """Stub for test_login_exception (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def package_error() -> None:
    """Stub for test_package_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def summary_error() -> None:
    """Stub for test_summary_error (port deferred)."""
