"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_without_mac_address() -> None:
    """Stub for test_device_without_mac_address."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""

