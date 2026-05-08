"""Tryke skip stub for test_device.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device() -> None:
    """Stub for test_device."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_failures() -> None:
    """Stub for test_device_failures."""

