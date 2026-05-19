"""The tests for media_player recorder."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import media_player
from homeassistant.components.media_player import (
    ATTR_ENTITY_PICTURE_LOCAL,
    ATTR_INPUT_SOURCE_LIST,
    ATTR_MEDIA_POSITION,
    ATTR_MEDIA_POSITION_UPDATED_AT,
    ATTR_SOUND_MODE_LIST,
)
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.const import ATTR_ENTITY_PICTURE, ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.media_player._fixtures import (
    media_player_only as media_player_only_fixture,
    recorder_mock as recorder_mock_fixture,
)
from tests.components.recorder.common import async_wait_recording_done
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _media_player_only: None = Depends(media_player_only_fixture),
    _recorder: Any = Depends(recorder_mock_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke fixture resolution before each test."""
    return hass


@test
async def exclude_attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test media_player registered attributes to be excluded."""
    now = dt_util.utcnow()
    expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()
    expect(
        await async_setup_component(
            hass, media_player.DOMAIN, {media_player.DOMAIN: {"platform": "demo"}}
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids()
    )
    expect(len(states) >= 1).to_be(True)
    for entity_states in states.values():
        for state in entity_states:
            expect(ATTR_ENTITY_PICTURE in state.attributes).to_be(False)
            expect(ATTR_ENTITY_PICTURE_LOCAL in state.attributes).to_be(False)
            expect(ATTR_FRIENDLY_NAME in state.attributes).to_be(True)
            expect(ATTR_INPUT_SOURCE_LIST in state.attributes).to_be(False)
            expect(ATTR_MEDIA_POSITION in state.attributes).to_be(False)
            expect(ATTR_MEDIA_POSITION_UPDATED_AT in state.attributes).to_be(False)
            expect(ATTR_SOUND_MODE_LIST in state.attributes).to_be(False)
