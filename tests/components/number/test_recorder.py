"""The tests for number recorder."""

from datetime import timedelta
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import number
from homeassistant.components.number import ATTR_MAX, ATTR_MIN, ATTR_MODE, ATTR_STEP
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.const import ATTR_FRIENDLY_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import recorder_mock as recorder_mock_fixture

from tests.common import async_fire_time_changed
from tests.components.recorder.common import async_wait_recording_done
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    recorder: Any = Depends(recorder_mock_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke fixture resolution before each test."""
    return hass


@test
async def exclude_attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test number registered attributes to be excluded."""
    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.NUMBER],
    ):
        expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()
        await async_setup_component(
            hass, number.DOMAIN, {number.DOMAIN: {"platform": "demo"}}
        )
        await hass.async_block_till_done()
        now = dt_util.utcnow()
        async_fire_time_changed(hass, now + timedelta(minutes=5))
        await hass.async_block_till_done()
        await async_wait_recording_done(hass)

        states = await hass.async_add_executor_job(
            get_significant_states, hass, now, None, hass.states.async_entity_ids()
        )
        expect(len(states) > 1).to_be_truthy()
        for entity_states in states.values():
            for state in entity_states:
                expect(ATTR_MIN in state.attributes).to_be_falsy()
                expect(ATTR_MAX in state.attributes).to_be_falsy()
                expect(ATTR_STEP in state.attributes).to_be_falsy()
                expect(ATTR_MODE in state.attributes).to_be_falsy()
                expect(ATTR_FRIENDLY_NAME in state.attributes).to_be_truthy()
