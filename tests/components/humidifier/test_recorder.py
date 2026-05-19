"""The tests for humidifier recorder."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import humidifier
from homeassistant.components.humidifier import (
    ATTR_AVAILABLE_MODES,
    ATTR_MAX_HUMIDITY,
    ATTR_MIN_HUMIDITY,
    ATTR_TARGET_HUMIDITY_STEP,
)
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant, split_entity_id
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.humidifier._fixtures import (
    recorder_mock as recorder_mock_fixture,
)
from tests.components.recorder.common import async_wait_recording_done
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: Any = Depends(recorder_mock_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke fixture resolution before each test."""
    return hass


@test
async def exclude_attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test humidifier registered attributes to be excluded."""
    now = dt_util.utcnow()
    expect(
        await async_setup_component(
            hass, humidifier.DOMAIN, {humidifier.DOMAIN: {"platform": "demo"}}
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
    for state in (
        state
        for entity_states in states.values()
        for state in entity_states
        if split_entity_id(state.entity_id)[0] == humidifier.DOMAIN
    ):
        expect(ATTR_MIN_HUMIDITY in state.attributes).to_be(False)
        expect(ATTR_MAX_HUMIDITY in state.attributes).to_be(False)
        expect(ATTR_AVAILABLE_MODES in state.attributes).to_be(False)
        expect(ATTR_FRIENDLY_NAME in state.attributes).to_be(True)
        expect(ATTR_TARGET_HUMIDITY_STEP in state.attributes).to_be(False)
