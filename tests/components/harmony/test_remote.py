"""Tryke skip stub for test_remote.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def connection_state_changes() -> None:
    """Stub for test_connection_state_changes."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remote_toggles() -> None:
    """Stub for test_remote_toggles."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_send_command() -> None:
    """Stub for test_async_send_command."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_send_command_custom_delay() -> None:
    """Stub for test_async_send_command_custom_delay."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def change_channel() -> None:
    """Stub for test_change_channel."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sync() -> None:
    """Stub for test_sync."""

