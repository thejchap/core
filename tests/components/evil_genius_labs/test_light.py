"""Tryke skip stub for test_light.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def works() -> None:
    """Stub for test_works."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_color() -> None:
    """Stub for test_turn_on_color."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_effect() -> None:
    """Stub for test_turn_on_effect."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_off() -> None:
    """Stub for test_turn_off."""

