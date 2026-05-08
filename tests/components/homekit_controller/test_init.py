"""Tryke skip-stubs for test_init.py - snapshot fixture coupling - needs pytest --snapshot-update."""

from tryke import test

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def unload_on_stop() -> None:
    """Stub for test_unload_on_stop."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def async_remove_entry() -> None:
    """Stub for test_async_remove_entry."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def device_remove_devices() -> None:
    """Stub for test_device_remove_devices."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def offline_device_raises() -> None:
    """Stub for test_offline_device_raises."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def ble_device_only_checks_is_available() -> None:
    """Stub for test_ble_device_only_checks_is_available."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def ble_device_populates_connections() -> None:
    """Stub for test_ble_device_populates_connections."""

@test.skip("snapshot fixture coupling - needs pytest --snapshot-update")
async def snapshots() -> None:
    """Stub for test_snapshots."""
