"""Tryke skip stub for test_number.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_value() -> None:
    """Stub for test_set_value."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_update() -> None:
    """Stub for test_state_update."""

