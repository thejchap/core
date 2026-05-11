"""Tests for Sonos services. (tryke skip stub)."""

from tryke import expect, fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.sonos.services module imports cleanly."""
    from homeassistant.components.sonos import services  # noqa: PLC0415
    expect(services).not_.to_be(None)


@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_player_join() -> None:
    """Stub for test_media_player_join (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_player_join_bad_entity() -> None:
    """Stub for test_media_player_join_bad_entity (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_player_join_entity_no_speaker() -> None:
    """Stub for test_media_player_join_entity_no_speaker (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_player_join_timeout() -> None:
    """Stub for test_media_player_join_timeout (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_player_unjoin_timeout() -> None:
    """Stub for test_media_player_unjoin_timeout (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_player_unjoin() -> None:
    """Stub for test_media_player_unjoin (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_player_unjoin_already_unjoined() -> None:
    """Stub for test_media_player_unjoin_already_unjoined (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def unjoin_completes_when_coordinator_receives_event_first() -> None:
    """Stub for test_unjoin_completes_when_coordinator_receives_event_first (port deferred)."""
