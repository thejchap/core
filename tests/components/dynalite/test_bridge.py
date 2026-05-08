"""Tryke skip stubs for test_bridge - sibling test pending port."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_device() -> None:
    """Stub for test_update_device (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def add_devices_then_register() -> None:
    """Stub for test_add_devices_then_register (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def register_then_add_devices() -> None:
    """Stub for test_register_then_add_devices (port deferred)."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notifications() -> None:
    """Stub for test_notifications (port deferred)."""


