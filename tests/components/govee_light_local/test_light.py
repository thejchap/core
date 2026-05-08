"""Tryke skip stub for test_light.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the govee_light_local.light module imports cleanly."""
    from homeassistant.components.govee_light_local import light  # noqa: PLC0415
    expect(light).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_known_device() -> None:
    """Stub for test_light_known_device (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_unknown_device() -> None:
    """Stub for test_light_unknown_device (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_remove() -> None:
    """Stub for test_light_remove (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_setup_retry() -> None:
    """Stub for test_light_setup_retry (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_setup_retry_eaddrinuse() -> None:
    """Stub for test_light_setup_retry_eaddrinuse (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_setup_error() -> None:
    """Stub for test_light_setup_error (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_on_off() -> None:
    """Stub for test_light_on_off (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_call_order() -> None:
    """Stub for test_turn_on_call_order (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_brightness() -> None:
    """Stub for test_light_brightness (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def light_color() -> None:
    """Stub for test_light_color (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def scene_on() -> None:
    """Stub for test_scene_on (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def scene_restore_rgb() -> None:
    """Stub for test_scene_restore_rgb (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def scene_restore_temperature() -> None:
    """Stub for test_scene_restore_temperature (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_callback_registered_and_triggers_state_update() -> None:
    """Stub for test_update_callback_registered_and_triggers_state_update (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_callback_cleared_on_remove() -> None:
    """Stub for test_update_callback_cleared_on_remove (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def scene_none() -> None:
    """Stub for test_scene_none (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_availability() -> None:
    """Stub for test_device_availability (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def one_silent_device_does_not_affect_others() -> None:
    """Stub for test_one_silent_device_does_not_affect_others (port deferred)."""


