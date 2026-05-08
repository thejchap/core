"""Tryke skip stub for test_switch.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fressnapf_tracker.switch module imports cleanly."""
    from homeassistant.components.fressnapf_tracker import switch  # noqa: PLC0415
    expect(switch).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_entity_device_snapshots() -> None:
    """Stub for test_state_entity_device_snapshots."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def not_added_when_no_energy_saving_mode() -> None:
    """Stub for test_not_added_when_no_energy_saving_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on() -> None:
    """Stub for test_turn_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_off() -> None:
    """Stub for test_turn_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_off_error() -> None:
    """Stub for test_turn_on_off_error."""

