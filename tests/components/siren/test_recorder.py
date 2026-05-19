"""The tests for siren recorder."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import siren
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.components.siren import ATTR_AVAILABLE_TONES
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant, split_entity_id
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.recorder.common import async_wait_recording_done
from tests.components.siren._fixtures import recorder_mock as recorder_mock_fixture
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    recorder: Any = Depends(recorder_mock_fixture),
) -> HomeAssistant:
    return hass


@test
async def exclude_attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test siren registered attributes to be excluded."""
    now = dt_util.utcnow()
    await async_setup_component(
        hass, siren.DOMAIN, {siren.DOMAIN: {"platform": "demo"}}
    )
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids()
    )
    expect(len(states) >= 1).to_be(True)
    for state in (
        state
        for entity_states in states.values()
        for state in entity_states
        if split_entity_id(state.entity_id)[0] == siren.DOMAIN
    ):
        expect(ATTR_AVAILABLE_TONES in state.attributes).to_be(False)
        expect(ATTR_FRIENDLY_NAME in state.attributes).to_be(True)
