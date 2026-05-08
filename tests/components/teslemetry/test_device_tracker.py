"""Tryke skip-stubs for teslemetry/test_device_tracker.py."""

from tryke import test


@test.skip("requires teslemetry API + snapshot — port deferred")
async def device_tracker() -> None:
    """Stub for test_device_tracker."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def device_tracker_alt() -> None:
    """Stub for test_device_tracker_alt."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def device_tracker_noscope() -> None:
    """Stub for test_device_tracker_noscope."""

@test.skip("requires teslemetry API + snapshot — port deferred")
async def device_tracker_streaming() -> None:
    """Stub for test_device_tracker_streaming."""

