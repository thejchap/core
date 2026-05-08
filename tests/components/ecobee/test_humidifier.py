"""Tryke skip stub for test_humidifier.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def attributes() -> None:
    """Stub for test_attributes."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on() -> None:
    """Stub for test_turn_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_off() -> None:
    """Stub for test_turn_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_mode() -> None:
    """Stub for test_set_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_humidity() -> None:
    """Stub for test_set_humidity."""

