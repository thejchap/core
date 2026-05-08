"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def airzone_create_switches() -> None:
    """Stub for test_airzone_create_switches."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def airzone_switch_off() -> None:
    """Stub for test_airzone_switch_off."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def airzone_switch_on() -> None:
    """Stub for test_airzone_switch_on."""

