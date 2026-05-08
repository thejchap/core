"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload_config_entry() -> None:
    """Stub for test_load_unload_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_setup_entry_authentication_error() -> None:
    """Stub for test_async_setup_entry_authentication_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def status_authentication_error_marks_device_offline() -> None:
    """Stub for test_status_authentication_error_marks_device_offline."""

