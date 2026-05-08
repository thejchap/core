"""Tryke skip stub for test_light.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_classic_led_ctrl() -> None:
    """Stub for test_setup_classic_led_ctrl."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def dynamic_new_devices() -> None:
    """Stub for test_dynamic_new_devices."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_off() -> None:
    """Stub for test_turn_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_brightness() -> None:
    """Stub for test_turn_on_brightness."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_effect() -> None:
    """Stub for test_turn_on_effect."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_update() -> None:
    """Stub for test_state_update."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_failed() -> None:
    """Stub for test_update_failed."""

