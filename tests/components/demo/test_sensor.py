"""Tryke skip stub for test_sensor.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def energy_sensor() -> None:
    """Stub for test_energy_sensor."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def restore_state() -> None:
    """Stub for test_restore_state."""

