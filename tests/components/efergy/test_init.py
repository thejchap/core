"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry_not_ready() -> None:
    """Stub for test_async_setup_entry_not_ready."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry_auth_failed() -> None:
    """Stub for test_async_setup_entry_auth_failed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_info() -> None:
    """Stub for test_device_info."""

