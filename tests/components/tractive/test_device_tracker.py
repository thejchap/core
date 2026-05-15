"""Tryke skip stub (snapshot test - port deferred)."""

from tryke import test


@test.skip("snapshot test - port deferred")
async def device_tracker() -> None:
    """Stub for test_device_tracker (port deferred)."""

@test.skip("snapshot test - port deferred")
async def source_type_phone() -> None:
    """Stub for test_source_type_phone (port deferred)."""

@test.skip("snapshot test - port deferred")
async def source_type_gps() -> None:
    """Stub for test_source_type_gps (port deferred)."""

@test.skip("snapshot test - port deferred")
async def device_tracker_with_empty_hw_info() -> None:
    """Stub for test_device_tracker_with_empty_hw_info (port deferred)."""
