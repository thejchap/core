"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reboot() -> None:
    """Stub for test_reboot."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def mark_calls_as_read() -> None:
    """Stub for test_mark_calls_as_read."""

