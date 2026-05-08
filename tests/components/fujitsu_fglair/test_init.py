"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def auth_failure() -> None:
    """Stub for test_auth_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def auth_regions() -> None:
    """Stub for test_auth_regions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def migrate_entry_v11_v12() -> None:
    """Stub for test_migrate_entry_v11_v12."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_auth_failure() -> None:
    """Stub for test_device_auth_failure."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_offline() -> None:
    """Stub for test_device_offline."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def token_expired() -> None:
    """Stub for test_token_expired."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def token_expiring_soon() -> None:
    """Stub for test_token_expiring_soon."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def startup_exception() -> None:
    """Stub for test_startup_exception."""

