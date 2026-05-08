"""Tryke skip stub for test_select.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def connection_state_changes() -> None:
    """Stub for test_connection_state_changes."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def options() -> None:
    """Stub for test_options."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def select_option() -> None:
    """Stub for test_select_option."""

