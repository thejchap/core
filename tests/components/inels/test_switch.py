"""Tryke skip-stubs for test_switch.py - indirect parametrize unsupported."""

from tryke import test

@test.skip("indirect parametrize unsupported")
async def switch_availability() -> None:
    """Stub for test_switch_availability."""

@test.skip("indirect parametrize unsupported")
async def switch_turn_on() -> None:
    """Stub for test_switch_turn_on."""

@test.skip("indirect parametrize unsupported")
async def switch_turn_off() -> None:
    """Stub for test_switch_turn_off."""
