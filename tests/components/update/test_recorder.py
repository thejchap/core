"""The tests for update recorder."""

from datetime import timedelta
from typing import Any

from tryke import Depends, expect, fixture, test

from homeassistant.components.recorder.history import get_significant_states
from homeassistant.components.update import UpdateEntityFeature
from homeassistant.components.update.const import (
    ATTR_DISPLAY_PRECISION,
    ATTR_IN_PROGRESS,
    ATTR_INSTALLED_VERSION,
    ATTR_RELEASE_SUMMARY,
    ATTR_UPDATE_PERCENTAGE,
    DOMAIN,
)
from homeassistant.const import ATTR_ENTITY_PICTURE, CONF_PLATFORM
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from .common import MockUpdateEntity

from tests.common import async_fire_time_changed, setup_test_component_platform
from tests.components.recorder.common import async_wait_recording_done
from tests.components.update._fixtures import recorder_mock as recorder_mock_fixture
from tests.hass_fixtures import hass as hass_fixture


def _build_mock_update_entities() -> list[MockUpdateEntity]:
    """Return the mock update entities the test cares about.

    Mirrors the relevant subset of the pytest ``mock_update_entities`` conftest
    fixture — only the "Update Already in Progress" entity is asserted on.
    """
    return [
        MockUpdateEntity(
            name="Update Already in Progress",
            unique_id="update_already_in_progress",
            installed_version="1.0.0",
            latest_version="1.0.1",
            in_progress=True,
            supported_features=UpdateEntityFeature.INSTALL
            | UpdateEntityFeature.PROGRESS,
            update_percentage=50,
        ),
    ]


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
    """Test update attributes to be excluded."""
    mock_update_entities = _build_mock_update_entities()
    now = dt_util.utcnow()
    setup_test_component_platform(hass, DOMAIN, mock_update_entities)
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()
    state = hass.states.get("update.update_already_in_progress")
    expect(state.attributes[ATTR_DISPLAY_PRECISION]).to_equal(0)
    expect(state.attributes[ATTR_IN_PROGRESS]).to_be(True)
    expect(state.attributes[ATTR_UPDATE_PERCENTAGE]).to_equal(50)
    expect(state.attributes[ATTR_ENTITY_PICTURE]).to_equal(
        "/api/brands/integration/test/icon.png"
    )
    await async_setup_component(hass, DOMAIN, {})

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
            expect(ATTR_DISPLAY_PRECISION in state.attributes).to_be(False)
            expect(ATTR_ENTITY_PICTURE in state.attributes).to_be(False)
            expect(ATTR_IN_PROGRESS in state.attributes).to_be(False)
            expect(ATTR_RELEASE_SUMMARY in state.attributes).to_be(False)
            expect(ATTR_INSTALLED_VERSION in state.attributes).to_be(True)
            expect(ATTR_UPDATE_PERCENTAGE in state.attributes).to_be(False)
