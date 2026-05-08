"""Tryke skip-stubs for test_switch.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def state() -> None:
    """Stub for test_state."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def turn_on() -> None:
    """Stub for test_turn_on."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def turn_off() -> None:
    """Stub for test_turn_off."""
