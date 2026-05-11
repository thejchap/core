"""Tryke skip stub for test_switch.py."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.ecobee.switch module imports cleanly."""
    from homeassistant.components.ecobee import switch  # noqa: PLC0415
    expect(switch).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def ventilator_20min_attributes() -> None:
    """Stub for test_ventilator_20min_attributes."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def ventilator_20min_when_on() -> None:
    """Stub for test_ventilator_20min_when_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def ventilator_20min_when_off() -> None:
    """Stub for test_ventilator_20min_when_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def ventilator_20min_when_empty() -> None:
    """Stub for test_ventilator_20min_when_empty."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_on_20min_ventilator() -> None:
    """Stub for test_turn_on_20min_ventilator."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_off_20min_ventilator() -> None:
    """Stub for test_turn_off_20min_ventilator."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def aux_heat_only_turn_on() -> None:
    """Stub for test_aux_heat_only_turn_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def aux_heat_only_turn_off() -> None:
    """Stub for test_aux_heat_only_turn_off."""

