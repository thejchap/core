"""Tryke skip stub for test_climate.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def climate() -> None:
    """Stub for test_climate."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def climate_set_temperature_turn_off_turn_on() -> None:
    """Stub for test_climate_set_temperature_turn_off_turn_on."""

