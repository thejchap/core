"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def data_validation() -> None:
    """Stub for test_data_validation (port deferred)."""

@test.skip("pending tryke port")
async def gps_enter_and_exit_home() -> None:
    """Stub for test_gps_enter_and_exit_home (port deferred)."""

@test.skip("pending tryke port")
async def beacon_enter_and_exit_home() -> None:
    """Stub for test_beacon_enter_and_exit_home (port deferred)."""

@test.skip("pending tryke port")
async def beacon_enter_and_exit_car() -> None:
    """Stub for test_beacon_enter_and_exit_car (port deferred)."""

@test.skip("pending tryke port")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry (port deferred)."""
