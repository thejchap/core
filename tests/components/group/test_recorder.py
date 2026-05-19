"""The tests for group recorder (tryke port)."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components import group
from homeassistant.components.group import ATTR_AUTO, ATTR_ENTITY_ID, ATTR_ORDER
from homeassistant.const import ATTR_FRIENDLY_NAME, STATE_ON
from homeassistant.core import HomeAssistant, split_entity_id
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.group._fixtures import recorder_mock as recorder_mock_fixture
from tests.components.recorder.common import async_wait_recording_done
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    _recorder: Any = Depends(recorder_mock_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke fixture resolution before each test."""
    return hass


@test
async def exclude_attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test number registered attributes to be excluded."""
    # Import get_significant_states lazily so the recorder module's import
    # side effects don't run before recorder_mock initializes the component.
    from homeassistant.components.recorder.history import (  # noqa: PLC0415
        get_significant_states,
    )

    now = dt_util.utcnow()
    hass.states.async_set("light.bowl", STATE_ON)

    expect(await async_setup_component(hass, "light", {})).to_be_truthy()
    expect(
        await async_setup_component(
            hass,
            group.DOMAIN,
            {
                group.DOMAIN: {
                    "group_zero": {"entities": "light.Bowl", "icon": "mdi:work"},
                    "group_one": {"entities": "light.Bowl", "icon": "mdi:work"},
                    "group_two": {"entities": "light.Bowl", "icon": "mdi:work"},
                }
            },
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
            if split_entity_id(state.entity_id)[0] == group.DOMAIN:
                expect(ATTR_AUTO not in state.attributes).to_be(True)
                expect(ATTR_ENTITY_ID not in state.attributes).to_be(True)
                expect(ATTR_ORDER not in state.attributes).to_be(True)
                expect(ATTR_FRIENDLY_NAME in state.attributes).to_be(True)
