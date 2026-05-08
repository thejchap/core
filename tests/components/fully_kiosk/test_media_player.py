"""Tryke skip stub for test_media_player.py."""

from tryke import test


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def media_player() -> None:
    """Stub for test_media_player."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def media_player_video() -> None:
    """Stub for test_media_player_video."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def media_player_unsupported() -> None:
    """Stub for test_media_player_unsupported."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def browse_media() -> None:
    """Stub for test_browse_media."""

