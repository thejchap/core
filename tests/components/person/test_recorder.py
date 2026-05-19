"""The tests for person recorder."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.person import ATTR_DEVICE_TRACKERS, DOMAIN
from homeassistant.components.recorder.history import get_significant_states
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.components.person._fixtures import (
    recorder_mock as recorder_mock_fixture,
    storage_setup as storage_setup_fixture,
)
from tests.components.recorder.common import async_wait_recording_done
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: Any = Depends(recorder_mock_fixture),
    _storage: Any = Depends(storage_setup_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Force tryke fixture resolution before each test."""
    return hass


@test
async def exclude_attributes(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test person attributes to be excluded."""
    now = dt_util.utcnow()
    config = {
        DOMAIN: {
            "id": "1234",
            "name": "test person",
            "user_id": "test_user_id",
            "device_trackers": ["device_tracker.test"],
        }
    }
    expect(await async_setup_component(hass, DOMAIN, config)).to_be_truthy()

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
            expect(ATTR_DEVICE_TRACKERS in state.attributes).to_be(False)
