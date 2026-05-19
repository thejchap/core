"""The tests for event recorder."""

from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import select
from homeassistant.components.event import ATTR_EVENT_TYPES
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.const import ATTR_FRIENDLY_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.components.event._fixtures import recorder_mock as recorder_mock_fixture
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
    """Test select registered attributes to be excluded."""
    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.EVENT],
    ):
        now = dt_util.utcnow()
        expect(await async_setup_component(hass, "homeassistant", {})).to_be_truthy()
        await async_setup_component(
            hass, select.DOMAIN, {select.DOMAIN: {"platform": "demo"}}
        )
        await hass.async_block_till_done()
        hass.bus.async_fire("demo_button_pressed")
        await hass.async_block_till_done()
        await async_wait_recording_done(hass)

        states = await hass.async_add_executor_job(
            get_significant_states, hass, now, None, hass.states.async_entity_ids()
        )
        expect(len(states) >= 1).to_be(True)
        for entity_states in states.values():
            for state in entity_states:
                expect(state).to_be_truthy()
                expect(ATTR_EVENT_TYPES in state.attributes).to_be(False)
                expect(ATTR_FRIENDLY_NAME in state.attributes).to_be(True)
