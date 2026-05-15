"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def binary_sensor() -> None:
    """Stub for test_binary_sensor (port deferred)."""

@test.skip("snapshot test - port deferred")
async def panel_faults() -> None:
    """Stub for test_panel_faults (port deferred)."""

@test.skip("snapshot test - port deferred")
async def area_ready_to_arm() -> None:
    """Stub for test_area_ready_to_arm (port deferred)."""
