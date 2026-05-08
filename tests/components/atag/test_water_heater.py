"""Tryke skip stub for test_water_heater.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def water_heater() -> None:
    """Stub for test_water_heater."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def setting_target_temperature() -> None:
    """Stub for test_setting_target_temperature."""

