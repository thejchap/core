"""Tryke skip stub for test_light.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_setup() -> None:
    """Stub for test_light_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_brightness() -> None:
    """Stub for test_light_brightness."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def zigbee_light_brightness() -> None:
    """Stub for test_zigbee_light_brightness."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_turn_off() -> None:
    """Stub for test_light_turn_off."""

