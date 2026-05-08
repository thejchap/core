"""Tests for the Switch as X Light platform. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def default_state() -> None:
    """Stub for test_default_state (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def light_service_calls() -> None:
    """Stub for test_light_service_calls (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def switch_service_calls() -> None:
    """Stub for test_switch_service_calls (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def light_service_calls_inverted() -> None:
    """Stub for test_light_service_calls_inverted (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def switch_service_calls_inverted() -> None:
    """Stub for test_switch_service_calls_inverted (port deferred)."""
