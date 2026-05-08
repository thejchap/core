"""Tryke skip stub for test_light.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fressnapf_tracker.light module imports cleanly."""
    from homeassistant.components.fressnapf_tracker import light  # noqa: PLC0415
    expect(light).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_entity_device_snapshots() -> None:
    """Stub for test_state_entity_device_snapshots."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def not_added_when_no_led() -> None:
    """Stub for test_not_added_when_no_led."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on() -> None:
    """Stub for test_turn_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_with_brightness() -> None:
    """Stub for test_turn_on_with_brightness."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_off() -> None:
    """Stub for test_turn_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_led_not_activatable() -> None:
    """Stub for test_turn_on_led_not_activatable."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_off_error() -> None:
    """Stub for test_turn_on_off_error."""

