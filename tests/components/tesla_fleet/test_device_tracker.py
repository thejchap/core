"""Tryke skip-stubs for tesla_fleet/test_device_tracker.py."""

from tryke import test


@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def device_tracker() -> None:
    """Stub for test_device_tracker."""

@test.skip("requires tesla_fleet OAuth + snapshot — port deferred")
async def device_tracker_offline() -> None:
    """Stub for test_device_tracker_offline."""

