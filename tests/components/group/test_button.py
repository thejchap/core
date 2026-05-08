"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def default_state() -> None:
    """Stub for test_default_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_reporting() -> None:
    """Stub for test_state_reporting."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_calls() -> None:
    """Stub for test_service_calls."""

