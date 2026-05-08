"""Tests for SLZB-Ultima infrared entity. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def infrared_setup_ultima() -> None:
    """Stub for test_infrared_setup_ultima (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def infrared_not_created_non_ultima() -> None:
    """Stub for test_infrared_not_created_non_ultima (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def infrared_send_command() -> None:
    """Stub for test_infrared_send_command (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def infrared_send_command_error() -> None:
    """Stub for test_infrared_send_command_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def infrared_send_empty_command_error() -> None:
    """Stub for test_infrared_send_empty_command_error (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def infrared_state_updated_after_send() -> None:
    """Stub for test_infrared_state_updated_after_send (port deferred)."""
