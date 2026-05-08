"""Tryke skip stub for test_media_player.py with one passing smoke test."""

from tryke import expect, test


@test
def module_importable() -> None:
    """Smoke test: the forked_daapd.media_player module imports cleanly."""
    from homeassistant.components.forked_daapd import media_player  # noqa: PLC0415
    expect(media_player).not_.to_be(None)


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unload_config_entry() -> None:
    """Stub for test_unload_config_entry."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def master_state() -> None:
    """Stub for test_master_state."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def no_update_when_get_request_returns_none() -> None:
    """Stub for test_no_update_when_get_request_returns_none."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def zone() -> None:
    """Stub for test_zone."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def last_outputs_master() -> None:
    """Stub for test_last_outputs_master."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def bunch_of_stuff_master() -> None:
    """Stub for test_bunch_of_stuff_master."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_play_media_from_paused() -> None:
    """Stub for test_async_play_media_from_paused."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_play_media_announcement_from_stopped() -> None:
    """Stub for test_async_play_media_announcement_from_stopped."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_play_media_unsupported() -> None:
    """Stub for test_async_play_media_unsupported."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_play_media_announcement_tts_timeout() -> None:
    """Stub for test_async_play_media_announcement_tts_timeout."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def use_pipe_control_with_no_api() -> None:
    """Stub for test_use_pipe_control_with_no_api."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def clear_source() -> None:
    """Stub for test_clear_source."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def librespot_java_stuff() -> None:
    """Stub for test_librespot_java_stuff."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def librespot_java_play_announcement() -> None:
    """Stub for test_librespot_java_play_announcement."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def librespot_java_play_media_pause_timeout() -> None:
    """Stub for test_librespot_java_play_media_pause_timeout."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def unsupported_update() -> None:
    """Stub for test_unsupported_update."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def invalid_websocket_port() -> None:
    """Stub for test_invalid_websocket_port."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def websocket_disconnect() -> None:
    """Stub for test_websocket_disconnect."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def async_play_media_enqueue() -> None:
    """Stub for test_async_play_media_enqueue."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def play_owntone_media() -> None:
    """Stub for test_play_owntone_media."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def play_spotify_media() -> None:
    """Stub for test_play_spotify_media."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def play_media_source() -> None:
    """Stub for test_play_media_source."""

