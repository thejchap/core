"""Tests for the Switch as X Fan platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def default_state() -> None:
    """Stub for test_default_state (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def service_calls() -> None:
    """Stub for test_service_calls (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def service_calls_inverted() -> None:
    """Stub for test_service_calls_inverted (port deferred)."""
