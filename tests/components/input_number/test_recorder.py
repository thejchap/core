"""The tests for recorder platform."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.input_number import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_MODE,
    ATTR_STEP,
    DOMAIN,
)
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.const import ATTR_EDITABLE
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.input_number._fixtures import (
    recorder_mock as recorder_mock_fixture,
)
from tests.components.recorder.common import async_wait_recording_done
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
    """Test attributes to be excluded."""
    now = dt_util.utcnow()
    expect(
        await async_setup_component(
            hass, DOMAIN, {DOMAIN: {"test": {"min": 0, "max": 100}}}
        )
    ).to_be_truthy()

    state = hass.states.get("input_number.test")
    expect(state).not_.to_be_none()
    expect(state.attributes[ATTR_EDITABLE]).to_be(False)
    expect(state.attributes[ATTR_MIN]).to_equal(0)
    expect(state.attributes[ATTR_MAX]).to_equal(100)
    expect(state.attributes[ATTR_STEP]).to_equal(1)
    expect(state.attributes[ATTR_MODE]).to_equal("slider")

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
            expect(ATTR_EDITABLE in state.attributes).to_be(False)
            expect(ATTR_MIN in state.attributes).to_be(False)
            expect(ATTR_MAX in state.attributes).to_be(False)
            expect(ATTR_STEP in state.attributes).to_be(False)
            expect(ATTR_MODE in state.attributes).to_be(False)
