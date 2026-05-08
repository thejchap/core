"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def buttons() -> None:
    """Stub for test_buttons."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sync_clock() -> None:
    """Stub for test_sync_clock."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def sync_clock_error_handling() -> None:
    """Stub for test_sync_clock_error_handling."""

