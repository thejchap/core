"""Tryke skip stub for test_media_player.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_unique_id() -> None:
    """Stub for test_set_unique_id."""

