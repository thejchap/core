"""Tryke skip stub for test_coordinator.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def logging_in_coordinator_first_update_data() -> None:
    """Stub for test_logging_in_coordinator_first_update_data."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def logging_in_coordinator_subsequent_update_data() -> None:
    """Stub for test_logging_in_coordinator_subsequent_update_data."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def logging_when_warming_up_sensor_present() -> None:
    """Stub for test_logging_when_warming_up_sensor_present."""

