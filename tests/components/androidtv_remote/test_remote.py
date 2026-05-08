"""Tryke skip stub for test_remote.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remote_receives_push_updates() -> None:
    """Stub for test_remote_receives_push_updates."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remote_toggles() -> None:
    """Stub for test_remote_toggles."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remote_send_command() -> None:
    """Stub for test_remote_send_command."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remote_send_command_multiple() -> None:
    """Stub for test_remote_send_command_multiple."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remote_send_command_with_hold_secs() -> None:
    """Stub for test_remote_send_command_with_hold_secs."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remote_connection_closed() -> None:
    """Stub for test_remote_connection_closed."""

