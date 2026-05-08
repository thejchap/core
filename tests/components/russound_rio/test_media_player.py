"""Tests for the Russound RIO media player. (tryke skip stub)."""

from tryke import fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test.skip("conftest fixtures need migration to _fixtures.py")
async def entity_state() -> None:
    """Stub for test_entity_state (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_volume() -> None:
    """Stub for test_media_volume (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def volume_mute() -> None:
    """Stub for test_volume_mute (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def source_service() -> None:
    """Stub for test_source_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def invalid_source_service() -> None:
    """Stub for test_invalid_source_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def power_service() -> None:
    """Stub for test_power_service (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_seek() -> None:
    """Stub for test_media_seek (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def play_media_preset_item_id() -> None:
    """Stub for test_play_media_preset_item_id (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def play_media_unknown_type() -> None:
    """Stub for test_play_media_unknown_type (port deferred)."""
