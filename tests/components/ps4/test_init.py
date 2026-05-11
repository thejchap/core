"""Tests for the PS4 Integration. (tryke skip stub)."""

from tryke import expect, fixture, test


@fixture
def _ensure_executor() -> None:
    """Force a HookExecutor for this module (tryke discovery quirk)."""


@test
def module_importable() -> None:
    """Smoke test: the homeassistant.components.ps4 module imports cleanly."""
    from homeassistant.components import ps4  # noqa: PLC0415
    expect(ps4).not_.to_be(None)


@test.skip("conftest fixtures need migration to _fixtures.py")
async def ps4_integration_setup() -> None:
    """Stub for test_ps4_integration_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def creating_entry_sets_up_media_player() -> None:
    """Stub for test_creating_entry_sets_up_media_player (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def config_flow_entry_migrate() -> None:
    """Stub for test_config_flow_entry_migrate (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def media_player_is_setup() -> None:
    """Stub for test_media_player_is_setup (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def games_reformat_to_dict() -> None:
    """Stub for test_games_reformat_to_dict (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def load_games() -> None:
    """Stub for test_load_games (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def loading_games_returns_dict() -> None:
    """Stub for test_loading_games_returns_dict (port deferred)."""

@test.skip("conftest fixtures need migration to _fixtures.py")
async def send_command() -> None:
    """Stub for test_send_command (port deferred)."""
