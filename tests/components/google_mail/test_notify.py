"""Tryke skip stub for test_notify.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify() -> None:
    """Stub for test_notify."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_voluptuous_error() -> None:
    """Stub for test_notify_voluptuous_error."""

