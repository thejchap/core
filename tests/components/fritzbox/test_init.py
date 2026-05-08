"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup() -> None:
    """Stub for test_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_unique_id() -> None:
    """Stub for test_update_unique_id."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_unique_id_no_change() -> None:
    """Stub for test_update_unique_id_no_change."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_remove() -> None:
    """Stub for test_unload_remove."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def logout_on_stop() -> None:
    """Stub for test_logout_on_stop."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remove_device() -> None:
    """Stub for test_remove_device."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def raise_config_entry_not_ready_when_offline() -> None:
    """Stub for test_raise_config_entry_not_ready_when_offline."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def raise_config_entry_error_when_login_fail() -> None:
    """Stub for test_raise_config_entry_error_when_login_fail."""

