"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_off() -> None:
    """Stub for test_turn_on_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_update() -> None:
    """Stub for test_state_update."""

