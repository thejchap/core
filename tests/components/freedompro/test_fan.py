"""Tryke skip stub for test_fan.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fan_get_state() -> None:
    """Stub for test_fan_get_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fan_set_off() -> None:
    """Stub for test_fan_set_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fan_set_on() -> None:
    """Stub for test_fan_set_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def fan_set_percent() -> None:
    """Stub for test_fan_set_percent."""

