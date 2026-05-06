"""Test state wrapper classes and helpers for Home Assistant templates."""

from __future__ import annotations

from datetime import timedelta

from tryke import Depends, expect, fixture, test

from homeassistant.const import STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.helpers import template
from homeassistant.helpers.json import json_dumps
from homeassistant.helpers.template import states as template_states
from homeassistant.util import dt as dt_util

from tests.common import async_fire_time_changed
from tests.hass_fixtures import hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def template_states_blocks_setitem(hass: HomeAssistant = Depends(hass)) -> None:
    """Test we cannot setitem on TemplateStates."""
    hass.states.async_set("light.new", STATE_ON)
    state = hass.states.get("light.new")
    template_state = template.TemplateState(hass, state, True)

    def _setitem() -> None:
        template_state["any"] = "any"

    expect(_setitem).to_raise(RuntimeError)


@test
async def template_states_can_serialize(hass: HomeAssistant = Depends(hass)) -> None:
    """Test TemplateState is serializable."""
    hass.states.async_set("light.new", STATE_ON)
    state = hass.states.get("light.new")
    template_state = template.TemplateState(hass, state, True)
    expect(template_state.as_dict() is template_state.as_dict()).to_be(True)
    expect(json_dumps(template_state)).to_equal(json_dumps(template_state))


@test
async def lru_increases_with_many_entities(hass: HomeAssistant = Depends(hass)) -> None:
    """Test that the template internal LRU cache increases with many entities."""
    # We do not actually want to record 4096 entities so we mock the entity count
    mock_entity_count = 16

    expect(template_states.CACHED_TEMPLATE_LRU.get_size()).to_equal(
        template_states.CACHED_TEMPLATE_STATES
    )
    expect(template_states.CACHED_TEMPLATE_NO_COLLECT_LRU.get_size()).to_equal(
        template_states.CACHED_TEMPLATE_STATES
    )
    template_states.CACHED_TEMPLATE_LRU.set_size(8)
    template_states.CACHED_TEMPLATE_NO_COLLECT_LRU.set_size(8)

    template.async_setup(hass)
    for i in range(mock_entity_count):
        hass.states.async_set(f"sensor.sensor{i}", "on")

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=10))
    await hass.async_block_till_done()

    expect(template_states.CACHED_TEMPLATE_LRU.get_size()).to_equal(
        int(round(mock_entity_count * template_states.ENTITY_COUNT_GROWTH_FACTOR))
    )
    expect(template_states.CACHED_TEMPLATE_NO_COLLECT_LRU.get_size()).to_equal(
        int(round(mock_entity_count * template_states.ENTITY_COUNT_GROWTH_FACTOR))
    )

    await hass.async_stop()

    for i in range(mock_entity_count):
        hass.states.async_set(f"sensor.sensor_add_{i}", "on")

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(minutes=20))
    await hass.async_block_till_done()

    expect(template_states.CACHED_TEMPLATE_LRU.get_size()).to_equal(
        int(round(mock_entity_count * template_states.ENTITY_COUNT_GROWTH_FACTOR))
    )
    expect(template_states.CACHED_TEMPLATE_NO_COLLECT_LRU.get_size()).to_equal(
        int(round(mock_entity_count * template_states.ENTITY_COUNT_GROWTH_FACTOR))
    )
