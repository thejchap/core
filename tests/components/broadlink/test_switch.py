"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def switch_setup_works() -> None:
    """Stub for test_switch_setup_works."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def switch_turn_off_turn_on() -> None:
    """Stub for test_switch_turn_off_turn_on."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def slots_switch_setup_works() -> None:
    """Stub for test_slots_switch_setup_works."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def slots_switch_turn_off_turn_on() -> None:
    """Stub for test_slots_switch_turn_off_turn_on."""

