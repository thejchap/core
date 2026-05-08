"""Tryke skip stub for test_media_player.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the fully_kiosk.media_player module imports cleanly."""
    from homeassistant.components.fully_kiosk import media_player  # noqa: PLC0415
    expect(media_player).not_.to_be(None)


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

