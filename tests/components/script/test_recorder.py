"""The tests for script recorder."""

from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import script
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.components.script import (
    ATTR_CUR,
    ATTR_LAST_ACTION,
    ATTR_LAST_TRIGGERED,
    ATTR_MAX,
    ATTR_MODE,
)
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import Context, HomeAssistant, ServiceCall, callback
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_mock_service
from tests.components.recorder.common import async_wait_recording_done
from tests.components.script._fixtures import recorder_mock as recorder_mock_fixture
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
    calls: list[ServiceCall] = async_mock_service(hass, "test", "automation")
    now = dt_util.utcnow()
    await hass.async_block_till_done()
    calls = []
    context = Context()

    @callback
    def record_call(service: ServiceCall) -> None:
        """Add recorded event to set."""
        calls.append(service)

    hass.services.async_register("test", "script", record_call)

    expect(
        await async_setup_component(
            hass,
            "script",
            {
                "script": {
                    "test": {
                        "sequence": {
                            "action": "test.script",
                            "data_template": {"hello": "{{ greeting }}"},
                        }
                    }
                }
            },
        )
    ).to_be_truthy()

    await hass.services.async_call(
        script.DOMAIN, "test", {"greeting": "world"}, context=context
    )
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)
    expect(len(calls)).to_equal(1)

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids()
    )
    expect(len(states) >= 1).to_be(True)
    for entity_states in states.values():
        for state in entity_states:
            expect(ATTR_LAST_TRIGGERED in state.attributes).to_be(False)
            expect(ATTR_MODE in state.attributes).to_be(False)
            expect(ATTR_CUR in state.attributes).to_be(False)
            expect(ATTR_LAST_ACTION in state.attributes).to_be(False)
            expect(ATTR_MAX in state.attributes).to_be(False)
            expect(ATTR_FRIENDLY_NAME in state.attributes).to_be(True)
