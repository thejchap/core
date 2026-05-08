"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_not_found_on_load_entry() -> None:
    """Stub for test_device_not_found_on_load_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def usb_error() -> None:
    """Stub for test_usb_error."""

