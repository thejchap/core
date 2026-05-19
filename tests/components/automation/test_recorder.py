"""The tests for automation recorder."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.automation import (
    ATTR_CUR,
    ATTR_LAST_TRIGGERED,
    ATTR_MAX,
    ATTR_MODE,
    CONF_ID,
)
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.const import ATTR_ENTITY_ID, ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_mock_service
from tests.components.automation._fixtures import recorder_mock as recorder_mock_fixture
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
    """Test automation registered attributes to be excluded."""
    calls = async_mock_service(hass, "test", "automation")
    now = dt_util.utcnow()
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "trigger": {"trigger": "event", "event_type": "test_event"},
                    "actions": {
                        "action": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(calls)).to_equal(1)
    expect(calls[0].data.get(ATTR_ENTITY_ID)).to_equal(["hello.world"])
    await async_wait_recording_done(hass)

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids()
    )
    expect(len(states)).to_equal(1)
    for entity_states in states.values():
        for state in entity_states:
            expect(ATTR_LAST_TRIGGERED in state.attributes).to_be(False)
            expect(ATTR_MODE in state.attributes).to_be(False)
            expect(ATTR_CUR in state.attributes).to_be(False)
            expect(CONF_ID in state.attributes).to_be(False)
            expect(ATTR_MAX in state.attributes).to_be(False)
            expect(ATTR_FRIENDLY_NAME in state.attributes).to_be(True)
