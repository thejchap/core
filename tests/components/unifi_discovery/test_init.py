"""Tryke skip stub (pending port)."""

from tryke import test


@test.skip("pending tryke port")
async def setup_starts_discovery() -> None:
    """Stub for test_setup_starts_discovery (port deferred)."""

@test.skip("pending tryke port")
async def setup_no_devices() -> None:
    """Stub for test_setup_no_devices (port deferred)."""

@test.skip("pending tryke port")
async def setup_device_without_mac() -> None:
    """Stub for test_setup_device_without_mac (port deferred)."""

@test.skip("pending tryke port")
async def dependency_loads_discovery() -> None:
    """Stub for test_dependency_loads_discovery (port deferred)."""

@test.skip("pending tryke port")
async def discovery_does_not_deepcopy_device() -> None:
    """Stub for test_discovery_does_not_deepcopy_device (port deferred)."""
