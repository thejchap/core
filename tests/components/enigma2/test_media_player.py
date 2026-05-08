"""Tests for the media player module."""

from unittest.mock import AsyncMock

from tryke import Depends, fixture, test

from homeassistant.components.media_player import (
    DOMAIN as MEDIA_PLAYER_DOMAIN,
)
from homeassistant.const import ATTR_ENTITY_ID, SERVICE_TURN_ON
from homeassistant.core import HomeAssistant

from ._fixtures import mock_config_entry, openwebif_device_mock

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def turn_on(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    device: AsyncMock = Depends(openwebif_device_mock),
) -> None:
    """Test turning on the media player."""
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    await hass.services.async_call(
        MEDIA_PLAYER_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "media_player.1_1_1_1"},
    )

    device.turn_on.assert_awaited_once()


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def turn_off() -> None:
    """Stub for test_turn_off."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def set_volume_level() -> None:
    """Stub for test_set_volume_level."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def volume_up() -> None:
    """Stub for test_volume_up."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def volume_down() -> None:
    """Stub for test_volume_down."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def remote_control_actions() -> None:
    """Stub for test_remote_control_actions."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def volume_mute() -> None:
    """Stub for test_volume_mute."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def select_source() -> None:
    """Stub for test_select_source."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_data_standby() -> None:
    """Stub for test_update_data_standby."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_volume() -> None:
    """Stub for test_update_volume."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def update_volume_none() -> None:
    """Stub for test_update_volume_none."""

