"""Tryke skip stub for test_media_player.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the frontier_silicon.media_player module imports cleanly."""
    from homeassistant.components.frontier_silicon import media_player  # noqa: PLC0415
    expect(media_player).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_media_previous_track_maps_errors() -> None:
    """Stub for test_async_media_previous_track_maps_errors (port deferred)."""


