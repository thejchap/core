"""Tryke skip stub for test_select.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_change() -> None:
    """Stub for test_state_change."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def select() -> None:
    """Stub for test_select."""

