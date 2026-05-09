"""The tests for the demo humidifier component."""

from collections.abc import AsyncGenerator
from unittest.mock import patch

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.components.humidifier import (
    ATTR_ACTION,
    ATTR_CURRENT_HUMIDITY,
    ATTR_HUMIDITY,
    ATTR_MAX_HUMIDITY,
    ATTR_MIN_HUMIDITY,
    DOMAIN as HUMIDITY_DOMAIN,
    MODE_AWAY,
    SERVICE_SET_HUMIDITY,
    SERVICE_SET_MODE,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_MODE,
    SERVICE_TOGGLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import expect_raises_async

ENTITY_DEHUMIDIFIER = "humidifier.dehumidifier"
ENTITY_HYGROSTAT = "humidifier.hygrostat"
ENTITY_HUMIDIFIER = "humidifier.humidifier"


@fixture
async def setup_demo_humidifier(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[None]:
    """Initialize setup demo humidifier."""
    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.HUMIDIFIER],
    ):
        await async_setup_component(hass, "homeassistant", {})
        assert await async_setup_component(
            hass, HUMIDITY_DOMAIN, {"humidifier": {"platform": "demo"}}
        )
        await hass.async_block_till_done()
        yield


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_demo_humidifier),
) -> HomeAssistant:
    return hass


@test
async def setup_params(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the initial parameters."""
    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes.get(ATTR_HUMIDITY)).to_equal(54.2)
    expect(state.attributes.get(ATTR_CURRENT_HUMIDITY)).to_equal(59.4)
    expect(state.attributes.get(ATTR_ACTION)).to_equal("drying")


@test
async def default_setup_params(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setup with default parameters."""
    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state.attributes.get(ATTR_MIN_HUMIDITY)).to_equal(0)
    expect(state.attributes.get(ATTR_MAX_HUMIDITY)).to_equal(100)


@test
async def set_target_humidity_bad_attr(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the target humidity without required attribute."""
    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state.attributes.get(ATTR_HUMIDITY)).to_equal(54.2)

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            HUMIDITY_DOMAIN,
            SERVICE_SET_HUMIDITY,
            {ATTR_HUMIDITY: None, ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER},
            blocking=True,
        )
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state.attributes.get(ATTR_HUMIDITY)).to_equal(54.2)


@test
async def set_target_humidity(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setting of the target humidity."""
    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state.attributes.get(ATTR_HUMIDITY)).to_equal(54.2)

    await hass.services.async_call(
        HUMIDITY_DOMAIN,
        SERVICE_SET_HUMIDITY,
        {ATTR_HUMIDITY: 64, ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state.attributes.get(ATTR_HUMIDITY)).to_equal(64)


@test
async def set_hold_mode_away(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the hold mode away."""
    await hass.services.async_call(
        HUMIDITY_DOMAIN,
        SERVICE_SET_MODE,
        {ATTR_MODE: MODE_AWAY, ATTR_ENTITY_ID: ENTITY_HYGROSTAT},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_HYGROSTAT)
    expect(state.attributes.get(ATTR_MODE)).to_equal(MODE_AWAY)


@test
async def set_hold_mode_eco(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the hold mode eco."""
    await hass.services.async_call(
        HUMIDITY_DOMAIN,
        SERVICE_SET_MODE,
        {ATTR_MODE: "eco", ATTR_ENTITY_ID: ENTITY_HYGROSTAT},
        blocking=True,
    )
    await hass.async_block_till_done()

    state = hass.states.get(ENTITY_HYGROSTAT)
    expect(state.attributes.get(ATTR_MODE)).to_equal("eco")


@test
async def turn_on(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn on device."""
    await hass.services.async_call(
        HUMIDITY_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER},
        blocking=True,
    )
    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes.get(ATTR_ACTION)).to_equal("off")

    await hass.services.async_call(
        HUMIDITY_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER},
        blocking=True,
    )
    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes.get(ATTR_ACTION)).to_equal("drying")


@test
async def turn_off(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn off device."""
    await hass.services.async_call(
        HUMIDITY_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER},
        blocking=True,
    )
    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes.get(ATTR_ACTION)).to_equal("drying")

    await hass.services.async_call(
        HUMIDITY_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER},
        blocking=True,
    )
    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state.state).to_equal(STATE_OFF)
    expect(state.attributes.get(ATTR_ACTION)).to_equal("off")


@test
async def toggle(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test toggle device."""
    await hass.services.async_call(
        HUMIDITY_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER},
        blocking=True,
    )
    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state.state).to_equal(STATE_ON)

    await hass.services.async_call(
        HUMIDITY_DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER},
        blocking=True,
    )
    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state.state).to_equal(STATE_OFF)

    await hass.services.async_call(
        HUMIDITY_DOMAIN,
        SERVICE_TOGGLE,
        {ATTR_ENTITY_ID: ENTITY_DEHUMIDIFIER},
        blocking=True,
    )
    state = hass.states.get(ENTITY_DEHUMIDIFIER)
    expect(state.state).to_equal(STATE_ON)
