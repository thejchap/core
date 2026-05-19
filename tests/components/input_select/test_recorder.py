"""The tests for recorder platform."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.input_select import ATTR_OPTIONS, DOMAIN
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.const import ATTR_EDITABLE
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.input_select._fixtures import (
    recorder_mock as recorder_mock_fixture,
)
from tests.components.recorder.common import async_wait_recording_done
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
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
            hass,
            DOMAIN,
            {
                DOMAIN: {
                    "test": {
                        "options": ["first option", "middle option", "last option"],
                        "initial": "middle option",
                    }
                }
            },
        )
    ).to_be_truthy()

    state = hass.states.get("input_select.test")
    expect(state).not_.to_be_none()
    expect(state.attributes[ATTR_EDITABLE]).to_be(False)

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
            expect(ATTR_OPTIONS in state.attributes).to_be(True)
