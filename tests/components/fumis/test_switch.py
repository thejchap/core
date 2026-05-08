"""Tryke skip stub for test_switch.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fumis.switch module imports cleanly."""
    from homeassistant.components.fumis import switch  # noqa: PLC0415
    expect(switch).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switches() -> None:
    """Stub for test_switches."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def eco_mode_turn_on() -> None:
    """Stub for test_eco_mode_turn_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def eco_mode_turn_off() -> None:
    """Stub for test_eco_mode_turn_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def timer_turn_on() -> None:
    """Stub for test_timer_turn_on."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def timer_turn_off() -> None:
    """Stub for test_timer_turn_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switch_error_handling() -> None:
    """Stub for test_switch_error_handling."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def switches_conditional_creation() -> None:
    """Stub for test_switches_conditional_creation."""

