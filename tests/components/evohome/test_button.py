"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def setup_platform() -> None:
    """Stub for test_setup_platform (port deferred)."""

@test.skip("snapshot test - port deferred")
async def system_reset_button_press() -> None:
    """Stub for test_system_reset_button_press (port deferred)."""

@test.skip("snapshot test - port deferred")
async def zone_reset_button_press() -> None:
    """Stub for test_zone_reset_button_press (port deferred)."""

@test.skip("snapshot test - port deferred")
async def dhw_reset_button_press() -> None:
    """Stub for test_dhw_reset_button_press (port deferred)."""
