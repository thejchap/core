"""Tryke skip stub for test_light.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_get_state() -> None:
    """Stub for test_light_get_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_set_on() -> None:
    """Stub for test_light_set_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_set_off() -> None:
    """Stub for test_light_set_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_set_brightness() -> None:
    """Stub for test_light_set_brightness."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_set_hue() -> None:
    """Stub for test_light_set_hue."""

