"""Tryke skip-stubs for test_init.py - sibling port deferred (132 LOC, 0 parametrize)."""

from tryke import test

@test.skip("sibling port deferred (132 LOC, 0 parametrize)")
async def setup_fails_on_missing_usb_port() -> None:
    """Stub for test_setup_fails_on_missing_usb_port."""

@test.skip("sibling port deferred (132 LOC, 0 parametrize)")
async def usb_device_reactivity() -> None:
    """Stub for test_usb_device_reactivity."""
