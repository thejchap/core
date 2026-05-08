"""Tryke skip stub for test_binary_sensor.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def is_off() -> None:
    """Stub for test_is_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update() -> None:
    """Stub for test_update."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_error() -> None:
    """Stub for test_update_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def discover_new_device() -> None:
    """Stub for test_discover_new_device."""

