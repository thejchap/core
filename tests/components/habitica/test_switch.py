"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch() -> None:
    """Stub for test_switch."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_off_toggle() -> None:
    """Stub for test_turn_on_off_toggle."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_off_toggle_exceptions() -> None:
    """Stub for test_turn_on_off_toggle_exceptions."""

