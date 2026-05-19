"""The tests for climate recorder."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import climate
from homeassistant.components.climate import (
    ATTR_FAN_MODES,
    ATTR_HVAC_MODES,
    ATTR_MAX_HUMIDITY,
    ATTR_MAX_TEMP,
    ATTR_MIN_HUMIDITY,
    ATTR_MIN_TEMP,
    ATTR_PRESET_MODES,
    ATTR_SWING_MODES,
    ATTR_TARGET_HUMIDITY_STEP,
    ATTR_TARGET_TEMP_STEP,
)
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.climate._fixtures import (
    climate_only as climate_only_fixture,
    recorder_mock as recorder_mock_fixture,
)
from tests.components.recorder.common import async_wait_recording_done
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _climate_only: None = Depends(climate_only_fixture),
    _recorder: Any = Depends(recorder_mock_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke fixture resolution before each test."""
    return hass


@test
async def exclude_attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test climate registered attributes to be excluded."""
    now = dt_util.utcnow()
    expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()
    expect(
        await async_setup_component(
            hass, climate.DOMAIN, {climate.DOMAIN: {"platform": "demo"}}
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids()
    )
    expect(len(states) > 1).to_be(True)
    for entity_states in states.values():
        for state in entity_states:
            expect(ATTR_FAN_MODES in state.attributes).to_be(False)
            expect(ATTR_FRIENDLY_NAME in state.attributes).to_be(True)
            expect(ATTR_HVAC_MODES in state.attributes).to_be(False)
            expect(ATTR_SWING_MODES in state.attributes).to_be(False)
            expect(ATTR_MAX_HUMIDITY in state.attributes).to_be(False)
            expect(ATTR_MAX_TEMP in state.attributes).to_be(False)
            expect(ATTR_MIN_HUMIDITY in state.attributes).to_be(False)
            expect(ATTR_MIN_TEMP in state.attributes).to_be(False)
            expect(ATTR_PRESET_MODES in state.attributes).to_be(False)
            expect(ATTR_TARGET_HUMIDITY_STEP in state.attributes).to_be(False)
            expect(ATTR_TARGET_TEMP_STEP in state.attributes).to_be(False)
