"""Tryke skip stub for test_switch.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def switches() -> None:
    """Stub for test_switches."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def switches_offline() -> None:
    """Stub for test_switches_offline."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def block_switch_availability() -> None:
    """Stub for test_block_switch_availability."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def toggle() -> None:
    """Stub for test_toggle."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setting_change() -> None:
    """Stub for test_setting_change."""

