"""Tests for the Spotify initialization. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_with_required_calls_failing() -> None:
    """Stub for test_setup_with_required_calls_failing (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def setup_free_account_is_failing() -> None:
    """Stub for test_setup_free_account_is_failing (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def oauth_implementation_not_available() -> None:
    """Stub for test_oauth_implementation_not_available (port deferred)."""
