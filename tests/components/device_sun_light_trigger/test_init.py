"""The tests device sun light trigger component."""

from datetime import datetime
from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import (
    device_sun_light_trigger,
    group,
    light,
)
from homeassistant.components.device_tracker import DOMAIN as DEVICE_TRACKER_DOMAIN
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_PLATFORM,
    EVENT_HOMEASSISTANT_START,
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_OFF,
    STATE_ON,
    STATE_UNKNOWN,
)
from homeassistant.core import CoreState, HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import scanner as scanner_fixture

from tests.common import async_fire_time_changed
from tests.hass_fixtures import (
    freezer as freezer_fixture,
    hass as hass_fixture,
)


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    return hass


@test
async def lights_on_when_sun_sets(
    hass: HomeAssistant = Depends(_trigger_executor),
    _scanner: None = Depends(scanner_fixture),
    freezer: Any = Depends(freezer_fixture),
) -> None:
    """Test lights go on when there is someone home and the sun sets."""
    test_time = datetime(2017, 4, 5, 1, 2, 3, tzinfo=dt_util.UTC)
    freezer.move_to(test_time)
    expect(
        await async_setup_component(
            hass,
            device_sun_light_trigger.DOMAIN,
            {device_sun_light_trigger.DOMAIN: {}},
        )
    ).to_be(True)

    await hass.services.async_call(
        light.DOMAIN,
        light.SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: "test.light"},
        blocking=True,
    )

    test_time = test_time.replace(hour=3)
    freezer.move_to(test_time)
    async_fire_time_changed(hass, test_time)
    await hass.async_block_till_done()

    expect(
        all(
            hass.states.get(ent_id).state == STATE_ON
            for ent_id in hass.states.async_entity_ids("light")
        )
    ).to_be(True)


@test
async def lights_turn_off_when_everyone_leaves(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test lights turn off when everyone leaves the house."""
    hass.data.pop("custom_components", None)  # equivalent of enable_custom_integrations
    expect(
        await async_setup_component(
            hass, "light", {light.DOMAIN: {CONF_PLATFORM: "test"}}
        )
    ).to_be(True)
    await hass.services.async_call(
        light.DOMAIN,
        light.SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "test.light"},
        blocking=True,
    )
    hass.states.async_set("device_tracker.bla", STATE_HOME)

    expect(
        await async_setup_component(
            hass,
            device_sun_light_trigger.DOMAIN,
            {device_sun_light_trigger.DOMAIN: {}},
        )
    ).to_be(True)

    hass.states.async_set("device_tracker.bla", STATE_NOT_HOME)

    await hass.async_block_till_done()

    expect(
        all(
            hass.states.get(ent_id).state == STATE_OFF
            for ent_id in hass.states.async_entity_ids("light")
        )
    ).to_be(True)


@test
async def lights_turn_on_when_coming_home_after_sun_set(
    hass: HomeAssistant = Depends(_trigger_executor),
    _scanner: None = Depends(scanner_fixture),
    freezer: Any = Depends(freezer_fixture),
) -> None:
    """Test lights turn on when coming home after sun set."""
    test_time = datetime(2017, 4, 5, 3, 2, 3, tzinfo=dt_util.UTC)
    freezer.move_to(test_time)
    await hass.services.async_call(
        light.DOMAIN, light.SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "all"}, blocking=True
    )

    expect(
        await async_setup_component(
            hass,
            device_sun_light_trigger.DOMAIN,
            {device_sun_light_trigger.DOMAIN: {}},
        )
    ).to_be(True)

    hass.states.async_set(f"{DEVICE_TRACKER_DOMAIN}.device_2", STATE_UNKNOWN)
    await hass.async_block_till_done()
    expect(
        all(
            hass.states.get(ent_id).state == STATE_OFF
            for ent_id in hass.states.async_entity_ids("light")
        )
    ).to_be(True)

    hass.states.async_set(f"{DEVICE_TRACKER_DOMAIN}.device_2", STATE_NOT_HOME)
    await hass.async_block_till_done()
    expect(
        all(
            hass.states.get(ent_id).state == STATE_OFF
            for ent_id in hass.states.async_entity_ids("light")
        )
    ).to_be(True)

    hass.states.async_set(f"{DEVICE_TRACKER_DOMAIN}.device_2", STATE_HOME)
    await hass.async_block_till_done()
    expect(
        all(
            hass.states.get(ent_id).state == light.STATE_ON
            for ent_id in hass.states.async_entity_ids("light")
        )
    ).to_be(True)


@test
async def lights_turn_on_when_coming_home_after_sun_set_person(
    hass: HomeAssistant = Depends(_trigger_executor),
    _scanner: None = Depends(scanner_fixture),
    freezer: Any = Depends(freezer_fixture),
) -> None:
    """Test lights turn on when coming home after sun set."""
    # Ensure all setup tasks are done (avoid flaky tests)
    await hass.async_block_till_done(wait_background_tasks=True)

    device_1 = f"{DEVICE_TRACKER_DOMAIN}.device_1"
    device_2 = f"{DEVICE_TRACKER_DOMAIN}.device_2"

    test_time = datetime(2017, 4, 5, 3, 2, 3, tzinfo=dt_util.UTC)
    freezer.move_to(test_time)
    await hass.services.async_call(
        light.DOMAIN, light.SERVICE_TURN_OFF, {ATTR_ENTITY_ID: "all"}, blocking=True
    )
    hass.states.async_set(device_1, STATE_NOT_HOME)
    hass.states.async_set(device_2, STATE_NOT_HOME)
    await hass.async_block_till_done()

    expect(
        all(
            not light.is_on(hass, ent_id)
            for ent_id in hass.states.async_entity_ids("light")
        )
    ).to_be(True)
    expect(hass.states.get(device_1).state).to_equal("not_home")
    expect(hass.states.get(device_2).state).to_equal("not_home")

    expect(
        await async_setup_component(
            hass,
            "person",
            {"person": [{"id": "me", "name": "Me", "device_trackers": [device_1]}]},
        )
    ).to_be(True)

    expect(await async_setup_component(hass, "group", {})).to_be(True)
    await hass.async_block_till_done()
    await group.Group.async_create_group(
        hass,
        "person_me",
        created_by_service=False,
        entity_ids=["person.me"],
        icon=None,
        mode=None,
        object_id=None,
        order=None,
    )

    expect(
        await async_setup_component(
            hass,
            device_sun_light_trigger.DOMAIN,
            {device_sun_light_trigger.DOMAIN: {"device_group": "group.person_me"}},
        )
    ).to_be(True)

    expect(
        all(
            hass.states.get(ent_id).state == STATE_OFF
            for ent_id in hass.states.async_entity_ids("light")
        )
    ).to_be(True)
    expect(hass.states.get(device_1).state).to_equal("not_home")
    expect(hass.states.get(device_2).state).to_equal("not_home")
    expect(hass.states.get("person.me").state).to_equal("not_home")

    # Unrelated device has no impact
    hass.states.async_set(device_2, STATE_HOME)
    await hass.async_block_till_done()

    expect(
        all(
            hass.states.get(ent_id).state == STATE_OFF
            for ent_id in hass.states.async_entity_ids("light")
        )
    ).to_be(True)
    expect(hass.states.get(device_1).state).to_equal("not_home")
    expect(hass.states.get(device_2).state).to_equal("home")
    expect(hass.states.get("person.me").state).to_equal("not_home")

    # person home switches on
    hass.states.async_set(device_1, STATE_HOME)
    await hass.async_block_till_done()
    await hass.async_block_till_done()

    expect(
        all(
            hass.states.get(ent_id).state == light.STATE_ON
            for ent_id in hass.states.async_entity_ids("light")
        )
    ).to_be(True)
    expect(hass.states.get(device_1).state).to_equal("home")
    expect(hass.states.get(device_2).state).to_equal("home")
    expect(hass.states.get("person.me").state).to_equal("home")


@test
async def initialize_start(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test we initialize when HA starts."""
    hass.set_state(CoreState.not_running)
    expect(
        await async_setup_component(
            hass,
            device_sun_light_trigger.DOMAIN,
            {device_sun_light_trigger.DOMAIN: {}},
        )
    ).to_be(True)

    with patch(
        "homeassistant.components.device_sun_light_trigger.activate_automation"
    ) as mock_activate:
        hass.bus.fire(EVENT_HOMEASSISTANT_START)
        await hass.async_block_till_done()
        await hass.async_block_till_done()

    expect(len(mock_activate.mock_calls)).to_equal(1)
