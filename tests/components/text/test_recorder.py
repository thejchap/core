"""The tests for text recorder."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import text
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.components.text import ATTR_MAX, ATTR_MIN, ATTR_MODE, ATTR_PATTERN
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.recorder.common import async_wait_recording_done
from tests.components.text._fixtures import (
    recorder_mock as recorder_mock_fixture,
    text_only as text_only_fixture,
)
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    recorder: Any = Depends(recorder_mock_fixture),
    _text_only: None = Depends(text_only_fixture),
) -> HomeAssistant:
    return hass


@test
async def exclude_attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test text registered attributes to be excluded."""
    now = dt_util.utcnow()
    expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()
    await async_setup_component(hass, text.DOMAIN, {text.DOMAIN: {"platform": "demo"}})
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
            for attr in (ATTR_MAX, ATTR_MIN, ATTR_MODE, ATTR_PATTERN):
                expect(attr in state.attributes).to_be(False)
            expect(ATTR_FRIENDLY_NAME in state.attributes).to_be(True)
