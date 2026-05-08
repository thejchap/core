"""Tryke skip stub for test_remote.py."""

from tryke import test


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remote_setup_works() -> None:
    """Stub for test_remote_setup_works."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remote_send_command() -> None:
    """Stub for test_remote_send_command."""


@test.skip("sibling test pending fixture migration to _fixtures.py")
async def remote_turn_off_turn_on() -> None:
    """Stub for test_remote_turn_off_turn_on."""

