"""Tryke skip stub for test_light.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def state_attributes() -> None:
    """Stub for test_state_attributes."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def turn_off() -> None:
    """Stub for test_turn_off."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def turn_off_without_entity_id() -> None:
    """Stub for test_turn_off_without_entity_id."""

