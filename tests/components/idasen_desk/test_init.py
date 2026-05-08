"""Tryke skip-stubs for test_init.py - sibling port deferred (98 LOC, 1 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (98 LOC, 1 parametrize)")
async def setup_and_shutdown() -> None:
    """Stub for test_setup_and_shutdown."""

@test.skip("sibling port deferred (98 LOC, 1 parametrize)")
async def setup_connect_exception() -> None:
    """Stub for test_setup_connect_exception."""

@test.skip("sibling port deferred (98 LOC, 1 parametrize)")
async def no_ble_device() -> None:
    """Stub for test_no_ble_device."""

@test.skip("sibling port deferred (98 LOC, 1 parametrize)")
async def reconnect_on_bluetooth_callback() -> None:
    """Stub for test_reconnect_on_bluetooth_callback."""

@test.skip("sibling port deferred (98 LOC, 1 parametrize)")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""
