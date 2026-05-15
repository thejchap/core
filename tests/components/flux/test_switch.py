"""The tests for the Flux switch platform."""

from datetime import date, datetime
from unittest.mock import patch

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.components import light, switch
from homeassistant.const import (
    ATTR_ENTITY_ID,
    CONF_PLATFORM,
    SERVICE_TURN_ON,
    STATE_ON,
    SUN_EVENT_SUNRISE,
)
from homeassistant.core import HomeAssistant, State
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import mock_light_entities, set_utc

from tests.common import (
    assert_setup_component,
    async_fire_time_changed,
    async_mock_service,
    mock_restore_cache,
    setup_test_component_platform,
)
from tests.components.light.common import MockLight
from tests.hass_fixtures import (
    entity_registry,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _utc: None = Depends(set_utc),
) -> None:
    """Anchor fixture; sets UTC for every test."""


@test
async def valid_config(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test configuration."""
    expect(
        await async_setup_component(
            hass,
            "switch",
            {
                "switch": {
                    "platform": "flux",
                    "name": "flux",
                    "lights": ["light.desk", "light.lamp"],
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()
    state = hass.states.get("switch.flux")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("off")


@test
async def unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    ent_reg: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test configuration with unique ID."""
    expect(
        await async_setup_component(
            hass,
            "switch",
            {
                "switch": {
                    "platform": "flux",
                    "name": "flux",
                    "lights": ["light.desk", "light.lamp"],
                    "unique_id": "zaphotbeeblebrox",
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()
    state = hass.states.get("switch.flux")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("off")

    expect(len(ent_reg.entities)).to_equal(1)
    expect(
        ent_reg.async_get_entity_id("switch", "flux", "zaphotbeeblebrox") is not None
    ).to_be(True)


@test
async def restore_state_last_on(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test restoring state when the last state is on."""
    mock_restore_cache(hass, [State("switch.flux", "on")])

    expect(
        await async_setup_component(
            hass,
            "switch",
            {
                "switch": {
                    "platform": "flux",
                    "name": "flux",
                    "lights": ["light.desk", "light.lamp"],
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("switch.flux")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("on")


@test
async def restore_state_last_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test restoring state when the last state is off."""
    mock_restore_cache(hass, [State("switch.flux", "off")])

    expect(
        await async_setup_component(
            hass,
            "switch",
            {
                "switch": {
                    "platform": "flux",
                    "name": "flux",
                    "lights": ["light.desk", "light.lamp"],
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("switch.flux")
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("off")


@test
async def valid_config_with_info(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test configuration."""
    expect(
        await async_setup_component(
            hass,
            "switch",
            {
                "switch": {
                    "platform": "flux",
                    "name": "flux",
                    "lights": ["light.desk", "light.lamp"],
                    "stop_time": "22:59",
                    "start_time": "7:22",
                    "start_colortemp": "1000",
                    "sunset_colortemp": "2000",
                    "stop_colortemp": "4000",
                }
            },
        )
    ).to_be(True)
    await hass.async_block_till_done()


@test
async def valid_config_no_name(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test configuration."""
    with assert_setup_component(1, "switch"):
        expect(
            await async_setup_component(
                hass,
                "switch",
                {"switch": {"platform": "flux", "lights": ["light.desk", "light.lamp"]}},
            )
        ).to_be(True)
        await hass.async_block_till_done()


@test
async def invalid_config_no_lights(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test configuration."""
    with assert_setup_component(0, "switch"):
        expect(
            await async_setup_component(
                hass, "switch", {"switch": {"platform": "flux", "name": "flux"}}
            )
        ).to_be(True)
        await hass.async_block_till_done()


async def _setup_light_platform(
    hass: HomeAssistant, lights: list[MockLight]
) -> MockLight:
    """Set up the test light platform and return the first light."""
    setup_test_component_platform(hass, light.DOMAIN, lights)
    await async_setup_component(
        hass, light.DOMAIN, {light.DOMAIN: {CONF_PLATFORM: "test"}}
    )
    await hass.async_block_till_done()

    ent1 = lights[0]
    state = hass.states.get(ent1.entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes.get("xy_color")).to_be(None)
    expect(state.attributes.get("brightness")).to_be(None)
    return ent1


def _make_event_date(sunrise_time, sunset_time):
    """Build a get_astral_event_date side_effect."""

    def event_date(
        hass: HomeAssistant, event: str, now: date | datetime | None = None
    ) -> datetime | None:
        if event == SUN_EVENT_SUNRISE:
            return sunrise_time
        return sunset_time

    return event_date


@test
async def flux_when_switch_is_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch when it is off."""
    ent1 = await _setup_light_platform(hass, lights)

    test_time = dt_util.utcnow().replace(hour=10, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)

    with (
        freeze_time(test_time),
        patch(
            "homeassistant.components.flux.switch.get_astral_event_date",
            side_effect=_make_event_date(sunrise_time, sunset_time),
        ),
    ):
        turn_on_calls = async_mock_service(hass, light.DOMAIN, SERVICE_TURN_ON)
        expect(
            await async_setup_component(
                hass,
                switch.DOMAIN,
                {
                    switch.DOMAIN: {
                        "platform": "flux",
                        "name": "flux",
                        "lights": [ent1.entity_id],
                    }
                },
            )
        ).to_be(True)
        await hass.async_block_till_done()
        async_fire_time_changed(hass, test_time)
        await hass.async_block_till_done()

    expect(bool(turn_on_calls)).to_be(False)


async def _run_flux_setup_and_turn_on(
    hass: HomeAssistant,
    ent1: MockLight,
    test_time: datetime,
    sunrise_time: datetime,
    sunset_time: datetime,
    extra_config: dict | None = None,
) -> list:
    """Set up flux switch, fire turn on, and return turn_on_calls."""
    config = {
        "platform": "flux",
        "name": "flux",
        "lights": [ent1.entity_id],
    }
    if extra_config:
        config.update(extra_config)
    with (
        freeze_time(test_time),
        patch(
            "homeassistant.components.flux.switch.get_astral_event_date",
            side_effect=_make_event_date(sunrise_time, sunset_time),
        ),
    ):
        await async_setup_component(
            hass,
            switch.DOMAIN,
            {switch.DOMAIN: config},
        )
        await hass.async_block_till_done()
        turn_on_calls = async_mock_service(hass, light.DOMAIN, SERVICE_TURN_ON)
        await hass.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.flux"},
            blocking=True,
        )
        async_fire_time_changed(hass, test_time)
        await hass.async_block_till_done()
    return turn_on_calls


@test
async def flux_before_sunrise(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch before sunrise."""
    ent1 = await _setup_light_platform(hass, lights)
    test_time = dt_util.utcnow().replace(hour=2, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=5)

    await hass.async_block_till_done()
    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass, ent1, test_time, sunrise_time, sunset_time
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(112)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.606, 0.379])


@test
async def flux_before_sunrise_known_location(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch before sunrise."""
    ent1 = await _setup_light_platform(hass, lights)

    hass.config.latitude = 55.948372
    hass.config.longitude = -3.199466
    hass.config.elevation = 17
    test_time = dt_util.utcnow().replace(
        hour=2, minute=0, second=0, day=21, month=6, year=2019
    )

    await hass.async_block_till_done()
    with freeze_time(test_time):
        expect(
            await async_setup_component(
                hass,
                switch.DOMAIN,
                {
                    switch.DOMAIN: {
                        "platform": "flux",
                        "name": "flux",
                        "lights": [ent1.entity_id],
                    }
                },
            )
        ).to_be(True)
        await hass.async_block_till_done()
        turn_on_calls = async_mock_service(hass, light.DOMAIN, SERVICE_TURN_ON)
        await hass.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.flux"},
            blocking=True,
        )
        async_fire_time_changed(hass, test_time)
        await hass.async_block_till_done()
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(112)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.606, 0.379])


@test
async def flux_after_sunrise_before_sunset(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch after sunrise and before sunset."""
    ent1 = await _setup_light_platform(hass, lights)
    test_time = dt_util.utcnow().replace(hour=8, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)
    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass, ent1, test_time, sunrise_time, sunset_time
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(173)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.439, 0.37])


@test
async def flux_after_sunset_before_stop(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch after sunset and before stop."""
    ent1 = await _setup_light_platform(hass, lights)
    test_time = dt_util.utcnow().replace(hour=17, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)
    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass,
        ent1,
        test_time,
        sunrise_time,
        sunset_time,
        extra_config={"stop_time": "22:00"},
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(146)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.506, 0.385])


@test
async def flux_after_stop_before_sunrise(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch after stop and before sunrise."""
    ent1 = await _setup_light_platform(hass, lights)
    test_time = dt_util.utcnow().replace(hour=23, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)
    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass, ent1, test_time, sunrise_time, sunset_time
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(112)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.606, 0.379])


@test
async def flux_with_custom_start_stop_times(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux with custom start and stop times."""
    ent1 = await _setup_light_platform(hass, lights)
    test_time = dt_util.utcnow().replace(hour=17, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)
    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass,
        ent1,
        test_time,
        sunrise_time,
        sunset_time,
        extra_config={"start_time": "6:00", "stop_time": "23:30"},
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(147)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.504, 0.385])


@test
async def flux_before_sunrise_stop_next_day(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch before sunrise, stop_time next day."""
    ent1 = await _setup_light_platform(hass, lights)
    test_time = dt_util.utcnow().replace(hour=2, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)
    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass,
        ent1,
        test_time,
        sunrise_time,
        sunset_time,
        extra_config={"stop_time": "01:00"},
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(112)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.606, 0.379])


@test
async def flux_after_sunrise_before_sunset_stop_next_day(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch after sunrise and before sunset, stop_time next day."""
    ent1 = await _setup_light_platform(hass, lights)
    test_time = dt_util.utcnow().replace(hour=8, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)
    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass,
        ent1,
        test_time,
        sunrise_time,
        sunset_time,
        extra_config={"stop_time": "01:00"},
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(173)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.439, 0.37])


@test
async def flux_after_sunset_before_midnight_stop_next_day(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch after sunset and before stop, stop_time next day."""
    ent1 = await _setup_light_platform(hass, lights)
    test_time = dt_util.utcnow().replace(hour=23, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)
    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass,
        ent1,
        test_time,
        sunrise_time,
        sunset_time,
        extra_config={"stop_time": "01:00"},
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(119)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.588, 0.386])


@test
async def flux_after_sunset_after_midnight_stop_next_day(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch after sunset and after midnight, stop_time next day."""
    ent1 = await _setup_light_platform(hass, lights)
    test_time = dt_util.utcnow().replace(hour=0, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)
    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass,
        ent1,
        test_time,
        sunrise_time,
        sunset_time,
        extra_config={"stop_time": "01:00"},
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(114)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.601, 0.382])


@test
async def flux_after_stop_before_sunrise_stop_next_day(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch after stop and before sunrise, stop_time next day."""
    ent1 = await _setup_light_platform(hass, lights)
    test_time = dt_util.utcnow().replace(hour=2, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)
    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass,
        ent1,
        test_time,
        sunrise_time,
        sunset_time,
        extra_config={"stop_time": "01:00"},
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(112)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.606, 0.379])


@test
async def flux_with_custom_colortemps(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux with custom start and stop colortemps."""
    ent1 = await _setup_light_platform(hass, lights)
    test_time = dt_util.utcnow().replace(hour=17, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)
    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass,
        ent1,
        test_time,
        sunrise_time,
        sunset_time,
        extra_config={
            "start_colortemp": "1000",
            "stop_colortemp": "6000",
            "stop_time": "22:00",
        },
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(159)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.469, 0.378])


@test
async def flux_with_custom_brightness(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux with custom start and stop colortemps."""
    ent1 = await _setup_light_platform(hass, lights)
    test_time = dt_util.utcnow().replace(hour=17, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)
    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass,
        ent1,
        test_time,
        sunrise_time,
        sunset_time,
        extra_config={"brightness": 255, "stop_time": "22:00"},
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(255)
    expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.506, 0.385])


@test
async def flux_with_multiple_lights(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch with multiple light entities."""
    setup_test_component_platform(hass, light.DOMAIN, lights)
    await async_setup_component(
        hass, light.DOMAIN, {light.DOMAIN: {CONF_PLATFORM: "test"}}
    )
    await hass.async_block_till_done()

    ent1, ent2, ent3 = lights

    await hass.services.async_call(
        light.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ent2.entity_id}, blocking=True
    )
    await hass.services.async_call(
        light.DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ent3.entity_id}, blocking=True
    )
    await hass.async_block_till_done()

    for ent in (ent1, ent2, ent3):
        state = hass.states.get(ent.entity_id)
        expect(state.state).to_equal(STATE_ON)
        expect(state.attributes.get("xy_color")).to_be(None)
        expect(state.attributes.get("brightness")).to_be(None)

    test_time = dt_util.utcnow().replace(hour=12, minute=0, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)

    with (
        freeze_time(test_time),
        patch(
            "homeassistant.components.flux.switch.get_astral_event_date",
            side_effect=_make_event_date(sunrise_time, sunset_time),
        ),
    ):
        await async_setup_component(
            hass,
            switch.DOMAIN,
            {
                switch.DOMAIN: {
                    "platform": "flux",
                    "name": "flux",
                    "lights": [ent1.entity_id, ent2.entity_id, ent3.entity_id],
                }
            },
        )
        await hass.async_block_till_done()
        turn_on_calls = async_mock_service(hass, light.DOMAIN, SERVICE_TURN_ON)
        await hass.services.async_call(
            switch.DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.flux"},
            blocking=True,
        )
        async_fire_time_changed(hass, test_time)
        await hass.async_block_till_done()
    for offset in (1, 2, 3):
        call = turn_on_calls[-offset]
        expect(call.data[light.ATTR_BRIGHTNESS]).to_equal(163)
        expect(call.data[light.ATTR_XY_COLOR]).to_equal([0.46, 0.376])


@test
async def flux_with_temp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch's mode mired."""
    setup_test_component_platform(hass, light.DOMAIN, lights)
    await async_setup_component(
        hass, light.DOMAIN, {light.DOMAIN: {CONF_PLATFORM: "test"}}
    )
    await hass.async_block_till_done()

    ent1 = lights[0]
    state = hass.states.get(ent1.entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes.get("color_temp")).to_be(None)

    test_time = dt_util.utcnow().replace(hour=8, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)

    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass,
        ent1,
        test_time,
        sunrise_time,
        sunset_time,
        extra_config={"mode": "mired"},
    )
    call = turn_on_calls[-1]
    expect(call.data[light.ATTR_COLOR_TEMP_KELVIN]).to_equal(3708)


@test
async def flux_with_rgb(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    lights: list[MockLight] = Depends(mock_light_entities),
) -> None:
    """Test the flux switch's mode rgb."""
    setup_test_component_platform(hass, light.DOMAIN, lights)
    await async_setup_component(
        hass, light.DOMAIN, {light.DOMAIN: {CONF_PLATFORM: "test"}}
    )
    await hass.async_block_till_done()

    ent1 = lights[0]
    state = hass.states.get(ent1.entity_id)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes.get("color_temp")).to_be(None)

    test_time = dt_util.utcnow().replace(hour=8, minute=30, second=0)
    sunset_time = test_time.replace(hour=17, minute=0, second=0)
    sunrise_time = test_time.replace(hour=5, minute=0, second=0)

    turn_on_calls = await _run_flux_setup_and_turn_on(
        hass,
        ent1,
        test_time,
        sunrise_time,
        sunset_time,
        extra_config={"mode": "rgb"},
    )
    call = turn_on_calls[-1]
    rgb = (255, 198, 152)
    rounded_call = tuple(map(round, call.data[light.ATTR_RGB_COLOR]))
    expect(rounded_call).to_equal(rgb)
