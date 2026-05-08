"""Tryke skip stub for test_button.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def button_press_sync_time() -> None:
    """Stub for test_button_press_sync_time."""

