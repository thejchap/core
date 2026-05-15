"""The tests for the time component."""

from datetime import time

from tryke import Depends, expect, fixture, test

from homeassistant.components.time import DOMAIN, SERVICE_SET_VALUE
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_TIME,
    CONF_PLATFORM,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from .common import MockTimeEntity

from tests.common import setup_test_component_platform
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def time_entity(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Test time entity."""
    entity = MockTimeEntity(
        name="test",
        unique_id="unique_time",
        native_value=time(1, 2, 3),
    )
    setup_test_component_platform(hass, DOMAIN, [entity])

    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    state = hass.states.get("time.test")
    expect(state.state).to_equal("01:02:03")
    expect(state.attributes).to_equal({ATTR_FRIENDLY_NAME: "test"})

    await hass.services.async_call(
        DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_TIME: time(2, 3, 4), ATTR_ENTITY_ID: "time.test"},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get("time.test")
    expect(state.state).to_equal("02:03:04")

    time_entity = MockTimeEntity(native_value=None)
    expect(time_entity.state).to_be(None)
    expect(time_entity.state_attributes).to_be(None)
