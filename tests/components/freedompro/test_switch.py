"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_get_state() -> None:
    """Stub for test_switch_get_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_set_off() -> None:
    """Stub for test_switch_set_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_set_on() -> None:
    """Stub for test_switch_set_on."""

