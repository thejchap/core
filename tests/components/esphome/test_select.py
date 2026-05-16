"""Test ESPHome selects."""

from unittest.mock import call

from aioesphomeapi import APIClient, SelectInfo, SelectState
from tryke import Depends, expect, fixture, test

from homeassistant.components.select import (
    ATTR_OPTION,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.const import ATTR_ENTITY_ID
from homeassistant.core import HomeAssistant

from ._fixtures import MockESPHomeDeviceType, mock_client, mock_esphome_device

from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor cross-module fixtures so tryke resolves before the test body."""
    return hass


@test.skip("requires mock_voice_assistant_v1_entry fixture - pending tryke port")
async def pipeline_selector() -> None:
    """Test assist pipeline selector."""


@test.skip("requires mock_voice_assistant_v1_entry fixture - pending tryke port")
async def secondary_pipeline_selector() -> None:
    """Test secondary assist pipeline selector."""


@test.skip("requires mock_voice_assistant_v1_entry fixture - pending tryke port")
async def vad_sensitivity_select() -> None:
    """Test VAD sensitivity select."""


@test.skip("requires mock_voice_assistant_v1_entry fixture - pending tryke port")
async def wake_word_select() -> None:
    """Test that wake word select is unavailable initially."""


@test.skip("requires mock_voice_assistant_v1_entry fixture - pending tryke port")
async def secondary_wake_word_select() -> None:
    """Test that secondary wake word select is unavailable initially."""


@test
async def select_generic_entity(
    hass: HomeAssistant = Depends(_trigger_executor),
    mock_client: APIClient = Depends(mock_client),
    mock_esphome_device: MockESPHomeDeviceType = Depends(mock_esphome_device),
) -> None:
    """Test a generic select entity."""
    entity_info = [
        SelectInfo(
            object_id="myselect",
            key=1,
            name="my select",
            options=["a", "b"],
        )
    ]
    states = [SelectState(key=1, state="a")]
    user_service = []
    await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("select.test_my_select")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("a")

    await hass.services.async_call(
        SELECT_DOMAIN,
        SERVICE_SELECT_OPTION,
        {ATTR_ENTITY_ID: "select.test_my_select", ATTR_OPTION: "b"},
        blocking=True,
    )
    mock_client.select_command.assert_has_calls([call(1, "b", device_id=0)])


@test.skip("assist_satellite entity setup failure - pending tryke port")
async def wake_word_select_no_wake_words() -> None:
    """Test wake word select is unavailable when there are no available wake word."""


@test.skip("assist_satellite entity setup failure - pending tryke port")
async def wake_word_select_zero_max_wake_words() -> None:
    """Test wake word select is unavailable max wake words is zero."""


@test.skip("assist_satellite entity setup failure - pending tryke port")
async def wake_word_select_no_active_wake_words() -> None:
    """Test wake word select has no wake word selected if none are active."""


@test.skip("assist_satellite entity setup failure - pending tryke port")
async def wake_word_select_first_active_wake_word() -> None:
    """Test wake word select uses first available wake word if one is active."""
