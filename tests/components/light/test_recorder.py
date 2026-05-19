"""The tests for light recorder."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import light
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_MODE,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_EFFECT_LIST,
    ATTR_HS_COLOR,
    ATTR_MAX_COLOR_TEMP_KELVIN,
    ATTR_MIN_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    ATTR_RGBW_COLOR,
    ATTR_RGBWW_COLOR,
    ATTR_SUPPORTED_COLOR_MODES,
    ATTR_XY_COLOR,
    DOMAIN,
)
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.light._fixtures import (
    light_only as light_only_fixture,
    recorder_mock as recorder_mock_fixture,
)
from tests.components.recorder.common import async_wait_recording_done
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _light_only: None = Depends(light_only_fixture),
    _recorder: Any = Depends(recorder_mock_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke fixture resolution before each test."""
    return hass


@test
async def exclude_attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test light registered attributes to be excluded."""
    now = dt_util.utcnow()
    expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()
    expect(
        await async_setup_component(
            hass, light.DOMAIN, {light.DOMAIN: {"platform": "demo"}}
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids(DOMAIN)
    )
    expect(len(states) >= 1).to_be(True)
    for entity_states in states.values():
        for state in entity_states:
            expect(ATTR_SUPPORTED_COLOR_MODES in state.attributes).to_be(False)
            expect(ATTR_EFFECT_LIST in state.attributes).to_be(False)
            expect(ATTR_FRIENDLY_NAME in state.attributes).to_be(True)
            expect(ATTR_MAX_COLOR_TEMP_KELVIN in state.attributes).to_be(False)
            expect(ATTR_MIN_COLOR_TEMP_KELVIN in state.attributes).to_be(False)
            expect(ATTR_BRIGHTNESS in state.attributes).to_be(False)
            expect(ATTR_COLOR_MODE in state.attributes).to_be(False)
            expect(ATTR_COLOR_TEMP_KELVIN in state.attributes).to_be(False)
            expect(ATTR_EFFECT in state.attributes).to_be(False)
            expect(ATTR_HS_COLOR in state.attributes).to_be(False)
            expect(ATTR_RGB_COLOR in state.attributes).to_be(False)
            expect(ATTR_RGBW_COLOR in state.attributes).to_be(False)
            expect(ATTR_RGBWW_COLOR in state.attributes).to_be(False)
            expect(ATTR_XY_COLOR in state.attributes).to_be(False)
