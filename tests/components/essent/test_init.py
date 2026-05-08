"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_entry() -> None:
    """Stub for test_load_unload_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_registry() -> None:
    """Stub for test_device_registry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_retry_on_error() -> None:
    """Stub for test_setup_retry_on_error."""

