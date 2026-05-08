"""Tryke skip stub for test_siren.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setup_params() -> None:
    """Stub for test_setup_params."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def all_setup_params() -> None:
    """Stub for test_all_setup_params."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def turn_on() -> None:
    """Stub for test_turn_on."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def turn_off() -> None:
    """Stub for test_turn_off."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def toggle() -> None:
    """Stub for test_toggle."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def turn_on_strip_attributes() -> None:
    """Stub for test_turn_on_strip_attributes."""

