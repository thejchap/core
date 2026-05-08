"""Tryke skip stub for test_coordinator.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_data_update_fails() -> None:
    """Stub for test_coordinator_data_update_fails."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_stale_device_serial_bridge() -> None:
    """Stub for test_coordinator_stale_device_serial_bridge."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def coordinator_stale_device_vedo() -> None:
    """Stub for test_coordinator_stale_device_vedo."""

