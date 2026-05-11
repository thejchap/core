"""Tryke skip-stubs for private_ble_device device_tracker tests.

Original tests use habluetooth advertisement injection + entity registry autouse; full port deferred.
"""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.private_ble_device.device_tracker module imports cleanly."""
    from homeassistant.components.private_ble_device import device_tracker  # noqa: PLC0415
    expect(device_tracker).not_.to_be(None)


@test.skip("habluetooth advertisement injection + entity registry autouse")
async def tracker_created() -> None:
    """Test creating a tracker entity when no devices have been seen."""

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def tracker_ignore_other_rpa() -> None:
    """Test that tracker ignores RPA's that don't match us."""

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def tracker_already_home() -> None:
    """Test creating a tracker and the device was already discovered by HA."""

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def tracker_arrive_home() -> None:
    """Test transition from not_home to home."""

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def tracker_isolation() -> None:
    """Test creating 2 tracker entities doesn't confuse anything."""

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def tracker_mac_rotate() -> None:
    """Test MAC address rotation."""

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def tracker_start_stale() -> None:
    """Test edge case where we find an existing stale record, and it expires before we see any more."""

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def tracker_leave_home() -> None:
    """Test tracker notices we have left."""

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def old_tracker_leave_home() -> None:
    """Test tracker ignores an old stale mac address timing out."""

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def mac_rotation() -> None:
    """Test sensors get value when we receive a broadcast."""
