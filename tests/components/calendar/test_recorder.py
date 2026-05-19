"""The tests for calendar recorder."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.recorder.history import get_significant_states
from homeassistant.const import ATTR_FRIENDLY_NAME
from homeassistant.core import HomeAssistant
from homeassistant.util import dt as dt_util

from tests.common import MockConfigEntry, async_fire_time_changed
from tests.components.calendar._fixtures import (
    config_entry as config_entry_fixture,
    mock_setup_integration as mock_setup_integration_fixture,
    recorder_mock as recorder_mock_fixture,
    set_time_zone as set_time_zone_fixture,
)
from tests.components.recorder.common import async_wait_recording_done
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: Any = Depends(recorder_mock_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    _time_zone: None = Depends(set_time_zone_fixture),
    _integration: None = Depends(mock_setup_integration_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> HomeAssistant:
    """Force tryke fixture resolution before each test and set up the entry."""
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()
    return hass


@test
async def exclude_attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test sensor attributes to be excluded."""
    now = dt_util.utcnow()

    state = hass.states.get("calendar.calendar_1")
    expect(state).to_be_truthy()
    expect(ATTR_FRIENDLY_NAME in state.attributes).to_be(True)
    expect("description" in state.attributes).to_be(True)

    # calendar.calendar_1
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done()
    await async_wait_recording_done(hass)

    states = await hass.async_add_executor_job(
        get_significant_states, hass, now, None, hass.states.async_entity_ids()
    )
    expect(len(states) > 1).to_be(True)
    for entity_states in states.values():
        for state in entity_states:
            expect(ATTR_FRIENDLY_NAME in state.attributes).to_be(True)
            expect("description" not in state.attributes).to_be(True)
