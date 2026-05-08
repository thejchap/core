"""The tests for the demo climate component."""

from collections.abc import AsyncGenerator
from unittest.mock import patch

import voluptuous as vol
from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import (
    ATTR_CURRENT_HUMIDITY,
    ATTR_CURRENT_TEMPERATURE,
    ATTR_FAN_MODE,
    ATTR_HUMIDITY,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_HVAC_MODES,
    ATTR_MAX_HUMIDITY,
    ATTR_MAX_TEMP,
    ATTR_MIN_HUMIDITY,
    ATTR_MIN_TEMP,
    ATTR_PRESET_MODE,
    ATTR_SWING_MODE,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    DOMAIN as CLIMATE_DOMAIN,
    PRESET_AWAY,
    PRESET_ECO,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HUMIDITY,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_SWING_MODE,
    SERVICE_SET_TEMPERATURE,
    HVACAction,
    HVACMode,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from homeassistant.util.unit_system import METRIC_SYSTEM

from tests.hass_fixtures import hass as hass_fixture
from tests.hass_tryke_helpers import expect_raises_async

ENTITY_CLIMATE = "climate.hvac"
ENTITY_ECOBEE = "climate.ecobee"
ENTITY_HEATPUMP = "climate.heatpump"


@fixture
async def setup_demo_climate(
    hass: HomeAssistant = Depends(hass_fixture),
) -> AsyncGenerator[None]:
    """Initialize setup demo climate."""
    with patch(
        "homeassistant.components.demo.COMPONENTS_WITH_CONFIG_ENTRY_DEMO_PLATFORM",
        [Platform.CLIMATE],
    ):
        hass.config.units = METRIC_SYSTEM
        await async_setup_component(hass, "homeassistant", {})
        assert await async_setup_component(
            hass, CLIMATE_DOMAIN, {"climate": {"platform": "demo"}}
        )
        await hass.async_block_till_done()
        yield


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: None = Depends(setup_demo_climate),
) -> HomeAssistant:
    return hass


@test
async def setup_params(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the initial parameters."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal(HVACMode.COOL)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(21)
    expect(state.attributes.get(ATTR_CURRENT_TEMPERATURE)).to_equal(22)
    expect(state.attributes.get(ATTR_FAN_MODE)).to_equal("on_high")
    expect(state.attributes.get(ATTR_HUMIDITY)).to_equal(67.4)
    expect(state.attributes.get(ATTR_CURRENT_HUMIDITY)).to_equal(54.2)
    expect(state.attributes.get(ATTR_SWING_MODE)).to_equal("off")
    expect(state.attributes.get(ATTR_HVAC_MODES)).to_equal(
        [
            HVACMode.OFF,
            HVACMode.HEAT,
            HVACMode.COOL,
            HVACMode.AUTO,
            HVACMode.DRY,
            HVACMode.FAN_ONLY,
        ]
    )


@test
async def default_setup_params(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setup with default parameters."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_MIN_TEMP)).to_equal(7)
    expect(state.attributes.get(ATTR_MAX_TEMP)).to_equal(35)
    expect(state.attributes.get(ATTR_MIN_HUMIDITY)).to_equal(30)
    expect(state.attributes.get(ATTR_MAX_HUMIDITY)).to_equal(99)


@test
async def set_only_target_temp_bad_attr(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the target temperature without required attribute."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(21)

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_TEMPERATURE: None},
            blocking=True,
        )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(21)


@test
async def set_only_target_temp(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setting of the target temperature."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(21)

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_TEMPERATURE: 30},
        blocking=True,
    )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(30.0)


@test
async def set_only_target_temp_with_convert(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setting of the target temperature."""
    state = hass.states.get(ENTITY_HEATPUMP)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(20)

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: ENTITY_HEATPUMP, ATTR_TEMPERATURE: 21},
        blocking=True,
    )

    state = hass.states.get(ENTITY_HEATPUMP)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(21.0)


@test
async def set_target_temp_range(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setting of the target temperature with range."""
    state = hass.states.get(ENTITY_ECOBEE)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_be(None)
    expect(state.attributes.get(ATTR_TARGET_TEMP_LOW)).to_equal(21.0)
    expect(state.attributes.get(ATTR_TARGET_TEMP_HIGH)).to_equal(24.0)

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: ENTITY_ECOBEE,
            ATTR_TARGET_TEMP_LOW: 20,
            ATTR_TARGET_TEMP_HIGH: 25,
        },
        blocking=True,
    )

    state = hass.states.get(ENTITY_ECOBEE)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_be(None)
    expect(state.attributes.get(ATTR_TARGET_TEMP_LOW)).to_equal(20.0)
    expect(state.attributes.get(ATTR_TARGET_TEMP_HIGH)).to_equal(25.0)


@test
async def set_target_temp_range_bad_attr(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the target temperature range without attribute."""
    state = hass.states.get(ENTITY_ECOBEE)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_be(None)
    expect(state.attributes.get(ATTR_TARGET_TEMP_LOW)).to_equal(21.0)
    expect(state.attributes.get(ATTR_TARGET_TEMP_HIGH)).to_equal(24.0)

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: ENTITY_ECOBEE,
                ATTR_TARGET_TEMP_LOW: None,
                ATTR_TARGET_TEMP_HIGH: None,
            },
            blocking=True,
        )

    state = hass.states.get(ENTITY_ECOBEE)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_be(None)
    expect(state.attributes.get(ATTR_TARGET_TEMP_LOW)).to_equal(21.0)
    expect(state.attributes.get(ATTR_TARGET_TEMP_HIGH)).to_equal(24.0)


@test
async def set_temp_with_hvac_mode(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setting of the hvac_mode in set_temperature."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(21)
    expect(state.state).to_equal(HVACMode.COOL)

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: ENTITY_CLIMATE,
            ATTR_TEMPERATURE: 23,
            ATTR_HVAC_MODE: HVACMode.OFF,
        },
        blocking=True,
    )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.state).to_equal(HVACMode.OFF)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(23)


@test
async def set_target_humidity_bad_attr(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the target humidity without required attribute."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_HUMIDITY)).to_equal(67.4)

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HUMIDITY,
            {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_HUMIDITY: None},
            blocking=True,
        )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_HUMIDITY)).to_equal(67.4)


@test
async def set_target_humidity(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test the setting of the target humidity."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_HUMIDITY)).to_equal(67.4)

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HUMIDITY,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_HUMIDITY: 64},
        blocking=True,
    )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_HUMIDITY)).to_equal(64.0)


@test
async def set_fan_mode_bad_attr(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting fan mode without required attribute."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_FAN_MODE)).to_equal("on_high")

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_FAN_MODE,
            {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_FAN_MODE: None},
            blocking=True,
        )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_FAN_MODE)).to_equal("on_high")


@test
async def set_fan_mode(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting of new fan mode."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_FAN_MODE)).to_equal("on_high")

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_FAN_MODE,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_FAN_MODE: "on_low"},
        blocking=True,
    )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_FAN_MODE)).to_equal("on_low")


@test
async def set_swing_mode_bad_attr(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting swing mode without required attribute."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_SWING_MODE)).to_equal("off")

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_SWING_MODE,
            {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_SWING_MODE: None},
            blocking=True,
        )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_SWING_MODE)).to_equal("off")


@test
async def set_swing(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting of new swing mode."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_SWING_MODE)).to_equal("off")

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_SWING_MODE,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_SWING_MODE: "auto"},
        blocking=True,
    )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_SWING_MODE)).to_equal("auto")


@test
async def set_hvac_bad_attr_and_state(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting hvac mode without required attribute."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_HVAC_ACTION)).to_equal(HVACAction.COOLING)
    expect(state.state).to_equal(HVACMode.COOL)

    async with expect_raises_async(vol.Invalid):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_HVAC_MODE: None},
            blocking=True,
        )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.attributes.get(ATTR_HVAC_ACTION)).to_equal(HVACAction.COOLING)
    expect(state.state).to_equal(HVACMode.COOL)


@test
async def set_hvac(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting of new hvac mode."""
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.state).to_equal(HVACMode.COOL)

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.state).to_equal(HVACMode.HEAT)


@test
async def set_hold_mode_away(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the hold mode away."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ECOBEE, ATTR_PRESET_MODE: PRESET_AWAY},
        blocking=True,
    )

    state = hass.states.get(ENTITY_ECOBEE)
    expect(state.attributes.get(ATTR_PRESET_MODE)).to_equal(PRESET_AWAY)


@test
async def set_hold_mode_eco(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test setting the hold mode eco."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ECOBEE, ATTR_PRESET_MODE: PRESET_ECO},
        blocking=True,
    )

    state = hass.states.get(ENTITY_ECOBEE)
    expect(state.attributes.get(ATTR_PRESET_MODE)).to_equal(PRESET_ECO)


@test
async def turn_on(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn on device."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.state).to_equal(HVACMode.OFF)

    await hass.services.async_call(
        CLIMATE_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: ENTITY_CLIMATE}, blocking=True
    )
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.state).to_equal(HVACMode.HEAT)


@test
async def turn_off(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test turn on device."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE, ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )

    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.state).to_equal(HVACMode.HEAT)

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_OFF,
        {ATTR_ENTITY_ID: ENTITY_CLIMATE},
        blocking=True,
    )
    state = hass.states.get(ENTITY_CLIMATE)
    expect(state.state).to_equal(HVACMode.OFF)
