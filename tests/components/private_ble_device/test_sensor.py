"""Tryke skip-stubs for private_ble_device sensor tests.

Original tests use habluetooth advertisement injection + entity registry autouse; full port deferred.
"""

from tryke import test

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def sensor_unavailable() -> None:
    """Test sensors are unavailable."""

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def sensors_already_home() -> None:
    """Test sensors get value when we start at home."""

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def sensors_come_home() -> None:
    """Test sensors get value when we receive a broadcast."""

@test.skip("habluetooth advertisement injection + entity registry autouse")
async def estimated_broadcast_interval() -> None:
    """Test sensors get value when we receive a broadcast."""
