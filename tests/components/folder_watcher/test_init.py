"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def invalid_path_setup() -> None:
    """Stub for test_invalid_path_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def valid_path_setup() -> None:
    """Stub for test_valid_path_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def event() -> None:
    """Stub for test_event."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def move_event() -> None:
    """Stub for test_move_event."""

