"""Tests for the Jellyfin media_player platform."""

from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.media_player import MediaPlayerState
from homeassistant.core import HomeAssistant

from ._fixtures import (
    init_integration,
    mock_api,
    mock_auth,
    mock_client,
    mock_config,
    mock_config_entry,
    mock_jellyfin,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def media_player(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _init: MockConfigEntry = Depends(init_integration),
    _jellyfin: MagicMock = Depends(mock_jellyfin),
    _api: MagicMock = Depends(mock_api),
) -> None:
    """Test the Jellyfin media player initial state."""
    state = hass.states.get("media_player.jellyfin_device")

    expect(state is not None).to_be(True)
    expect(state.state).to_equal(MediaPlayerState.PAUSED)


@test.skip("port deferred - sibling tests")
async def media_player_music() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def services() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def services_enqueue() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def services_shuffle() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def browse_media() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def search_media() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def new_client_connected() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def supports_media_control_fallback() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def set_volume_command_alternative() -> None:
    """Stub."""


@test.skip("port deferred - sibling tests")
async def mute_requires_both_commands() -> None:
    """Stub."""
