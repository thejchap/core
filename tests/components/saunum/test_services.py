"""Tests for Saunum services. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def start_session_success() -> None:
    """Stub for test_start_session_success (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def start_session_with_defaults() -> None:
    """Stub for test_start_session_with_defaults (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def start_session_door_open() -> None:
    """Stub for test_start_session_door_open (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def start_session_communication_error() -> None:
    """Stub for test_start_session_communication_error (port deferred)."""
