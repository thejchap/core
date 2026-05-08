"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def load_unload() -> None:
    """Stub for test_load_unload."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def refresh_expired_token() -> None:
    """Stub for test_refresh_expired_token."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def invalid_credentials() -> None:
    """Stub for test_invalid_credentials."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def raise_config_entry_not_ready_when_offline() -> None:
    """Stub for test_raise_config_entry_not_ready_when_offline."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def raise_config_entry_not_ready_when_offline_and_expired() -> None:
    """Stub for test_raise_config_entry_not_ready_when_offline_and_expired."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_config_entry() -> None:
    """Stub for test_migrate_config_entry."""

