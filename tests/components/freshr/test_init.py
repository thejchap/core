"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_entry() -> None:
    """Stub for test_unload_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_errors() -> None:
    """Stub for test_setup_errors."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_no_devices() -> None:
    """Stub for test_setup_no_devices."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stale_device_removed() -> None:
    """Stub for test_stale_device_removed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def stale_device_not_removed_on_poll_error() -> None:
    """Stub for test_stale_device_not_removed_on_poll_error."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def readings_login_error_triggers_reauth() -> None:
    """Stub for test_readings_login_error_triggers_reauth."""

