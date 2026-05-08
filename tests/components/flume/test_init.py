"""Tryke skip stub for test_init.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def setup_config_entry() -> None:
    """Stub for test_setup_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def device_list_timeout() -> None:
    """Stub for test_device_list_timeout."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reauth_when_unauthorized() -> None:
    """Stub for test_reauth_when_unauthorized."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def list_notifications_service() -> None:
    """Stub for test_list_notifications_service."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def list_notifications_service_config_entry_errors() -> None:
    """Stub for test_list_notifications_service_config_entry_errors."""

