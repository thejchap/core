"""Tryke skip stub for test_notify.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_file() -> None:
    """Stub for test_notify_file."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_file_not_allowed() -> None:
    """Stub for test_notify_file_not_allowed."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def notify_file_write_access_failed() -> None:
    """Stub for test_notify_file_write_access_failed."""

