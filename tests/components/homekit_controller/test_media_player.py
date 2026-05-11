"""Tryke skip-stubs for test_media_player.py - sibling port deferred (469 LOC, 0 parametrize)."""

from tryke import expect, test

@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.homekit_controller.media_player module imports cleanly."""
    from homeassistant.components.homekit_controller import media_player  # noqa: PLC0415
    expect(media_player).not_.to_be(None)


@test.skip("sibling port deferred (469 LOC, 0 parametrize)")
async def tv_read_state() -> None:
    """Stub for test_tv_read_state."""

@test.skip("sibling port deferred (469 LOC, 0 parametrize)")
async def tv_read_sources() -> None:
    """Stub for test_tv_read_sources."""

@test.skip("sibling port deferred (469 LOC, 0 parametrize)")
async def play_remote_key() -> None:
    """Stub for test_play_remote_key."""

@test.skip("sibling port deferred (469 LOC, 0 parametrize)")
async def pause_remote_key() -> None:
    """Stub for test_pause_remote_key."""

@test.skip("sibling port deferred (469 LOC, 0 parametrize)")
async def play() -> None:
    """Stub for test_play."""

@test.skip("sibling port deferred (469 LOC, 0 parametrize)")
async def pause() -> None:
    """Stub for test_pause."""

@test.skip("sibling port deferred (469 LOC, 0 parametrize)")
async def stop() -> None:
    """Stub for test_stop."""

@test.skip("sibling port deferred (469 LOC, 0 parametrize)")
async def tv_set_source() -> None:
    """Stub for test_tv_set_source."""

@test.skip("sibling port deferred (469 LOC, 0 parametrize)")
async def tv_set_source_fail() -> None:
    """Stub for test_tv_set_source_fail."""

@test.skip("sibling port deferred (469 LOC, 0 parametrize)")
async def migrate_unique_id() -> None:
    """Stub for test_migrate_unique_id."""

@test.skip("sibling port deferred (469 LOC, 0 parametrize)")
async def turn_on() -> None:
    """Stub for test_turn_on."""

@test.skip("sibling port deferred (469 LOC, 0 parametrize)")
async def turn_off() -> None:
    """Stub for test_turn_off."""
