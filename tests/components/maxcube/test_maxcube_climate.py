"""Test EQ3 Max! Thermostats."""

from datetime import timedelta
from unittest.mock import MagicMock

from maxcube.cube import MaxCube
from maxcube.device import (
    MAX_DEVICE_MODE_AUTOMATIC,
    MAX_DEVICE_MODE_BOOST,
    MAX_DEVICE_MODE_MANUAL,
    MAX_DEVICE_MODE_VACATION,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_HVAC_MODES,
    ATTR_MAX_TEMP,
    ATTR_MIN_TEMP,
    ATTR_PRESET_MODE,
    ATTR_PRESET_MODES,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    DOMAIN as CLIMATE_DOMAIN,
    PRESET_AWAY,
    PRESET_BOOST,
    PRESET_COMFORT,
    PRESET_ECO,
    PRESET_NONE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_PRESET_MODE,
    SERVICE_SET_TEMPERATURE,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.maxcube.climate import (
    MAX_TEMPERATURE,
    MIN_TEMPERATURE,
    OFF_TEMPERATURE,
    ON_TEMPERATURE,
    PRESET_ON,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    ATTR_TEMPERATURE,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import entity_registry as er
from homeassistant.util import utcnow

from ._fixtures import cube as cube_fx, thermostat as thermostat_fx, wallthermostat as wallthermostat_fx

from tests.common import async_fire_time_changed
from tests.hass_fixtures import entity_registry as entity_registry_fx, hass as hass_fixture
from tests.hass_tryke_helpers import expect_raises_async

ENTITY_ID = "climate.testroom_testthermostat"
WALL_ENTITY_ID = "climate.testroom_testwallthermostat"
VALVE_POSITION = "valve_position"


@fixture
def _trigger_executor() -> int:
    """Force tryke to build a per-module HookExecutor for this file."""
    return 0


@test
async def setup_thermostat(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    cube: MaxCube = Depends(cube_fx),
) -> None:
    """Test a successful setup of a thermostat device."""
    expect(entity_registry.async_is_registered(ENTITY_ID)).to_be(True)
    entity = entity_registry.async_get(ENTITY_ID)
    expect(entity.unique_id).to_equal("AABBCCDD01")

    state = hass.states.get(ENTITY_ID)
    expect(state.state).to_equal(HVACMode.AUTO)
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal("TestRoom TestThermostat")
    expect(state.attributes.get(ATTR_HVAC_ACTION)).to_equal(HVACAction.HEATING)
    expect(state.attributes.get(ATTR_HVAC_MODES)).to_equal(
        [HVACMode.OFF, HVACMode.AUTO, HVACMode.HEAT]
    )
    expect(state.attributes.get(ATTR_PRESET_MODES)).to_equal(
        [
            PRESET_NONE,
            PRESET_BOOST,
            PRESET_COMFORT,
            PRESET_ECO,
            PRESET_AWAY,
            PRESET_ON,
        ]
    )
    expect(state.attributes.get(ATTR_PRESET_MODE)).to_equal(PRESET_NONE)
    expect(state.attributes.get(ATTR_SUPPORTED_FEATURES)).to_equal(
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.PRESET_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    expect(state.attributes.get(ATTR_MAX_TEMP)).to_equal(MAX_TEMPERATURE)
    expect(state.attributes.get(ATTR_MIN_TEMP)).to_equal(5.0)
    expect(state.attributes.get(ATTR_CURRENT_TEMPERATURE)).to_equal(19.0)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(20.5)
    expect(state.attributes.get(VALVE_POSITION)).to_equal(25)


@test
async def setup_wallthermostat(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    cube: MaxCube = Depends(cube_fx),
) -> None:
    """Test a successful setup of a wall thermostat device."""
    expect(entity_registry.async_is_registered(WALL_ENTITY_ID)).to_be(True)
    entity = entity_registry.async_get(WALL_ENTITY_ID)
    expect(entity.unique_id).to_equal("AABBCCDD02")

    state = hass.states.get(WALL_ENTITY_ID)
    expect(state.state).to_equal(HVACMode.OFF)
    expect(state.attributes.get(ATTR_FRIENDLY_NAME)).to_equal(
        "TestRoom TestWallThermostat"
    )
    expect(state.attributes.get(ATTR_HVAC_ACTION)).to_equal(HVACAction.HEATING)
    expect(state.attributes.get(ATTR_PRESET_MODE)).to_equal(PRESET_NONE)
    expect(state.attributes.get(ATTR_MAX_TEMP)).to_equal(29.0)
    expect(state.attributes.get(ATTR_MIN_TEMP)).to_equal(5.0)
    expect(state.attributes.get(ATTR_CURRENT_TEMPERATURE)).to_equal(19.0)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_be(None)


@test
async def thermostat_set_hvac_mode_off(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    thermostat: MagicMock = Depends(thermostat_fx),
) -> None:
    """Turn off thermostat."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.OFF},
        blocking=True,
    )
    cube.set_temperature_mode.assert_called_once_with(
        thermostat, OFF_TEMPERATURE, MAX_DEVICE_MODE_MANUAL
    )

    thermostat.mode = MAX_DEVICE_MODE_MANUAL
    thermostat.target_temperature = OFF_TEMPERATURE
    thermostat.valve_position = 0

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    expect(state.state).to_equal(HVACMode.OFF)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_be(None)
    expect(state.attributes.get(ATTR_HVAC_ACTION)).to_equal(HVACAction.OFF)
    expect(state.attributes.get(VALVE_POSITION)).to_equal(0)

    wall_state = hass.states.get(WALL_ENTITY_ID)
    expect(wall_state.attributes.get(ATTR_HVAC_ACTION)).to_equal(HVACAction.OFF)


@test
async def thermostat_set_hvac_mode_heat(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    thermostat: MagicMock = Depends(thermostat_fx),
) -> None:
    """Set hvac mode to heat."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )
    cube.set_temperature_mode.assert_called_once_with(
        thermostat, 20.5, MAX_DEVICE_MODE_MANUAL
    )
    thermostat.mode = MAX_DEVICE_MODE_MANUAL

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    expect(state.state).to_equal(HVACMode.HEAT)


@test
async def thermostat_set_invalid_hvac_mode(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    thermostat: MagicMock = Depends(thermostat_fx),
) -> None:
    """Set hvac mode to invalid."""
    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_HVAC_MODE,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_HVAC_MODE: HVACMode.DRY},
            blocking=True,
        )
    cube.set_temperature_mode.assert_not_called()


@test
async def thermostat_set_temperature(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    thermostat: MagicMock = Depends(thermostat_fx),
) -> None:
    """Set temperature."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_TEMPERATURE: 10.0},
        blocking=True,
    )
    cube.set_temperature_mode.assert_called_once_with(thermostat, 10.0, None)
    thermostat.target_temperature = 10.0
    thermostat.valve_position = 0

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    expect(state.state).to_equal(HVACMode.AUTO)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(10.0)
    expect(state.attributes.get(ATTR_HVAC_ACTION)).to_equal(HVACAction.IDLE)


@test
async def thermostat_set_no_temperature(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    thermostat: MagicMock = Depends(thermostat_fx),
) -> None:
    """Set temperature without ATTR_TEMPERATURE."""
    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_TEMPERATURE,
            {
                ATTR_ENTITY_ID: ENTITY_ID,
                ATTR_TARGET_TEMP_HIGH: 29.0,
                ATTR_TARGET_TEMP_LOW: 10.0,
            },
            blocking=True,
        )
    cube.set_temperature_mode.assert_not_called()


@test
async def thermostat_set_preset_on(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    thermostat: MagicMock = Depends(thermostat_fx),
) -> None:
    """Set preset mode to on."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: PRESET_ON},
        blocking=True,
    )

    cube.set_temperature_mode.assert_called_once_with(
        thermostat, ON_TEMPERATURE, MAX_DEVICE_MODE_MANUAL
    )
    thermostat.mode = MAX_DEVICE_MODE_MANUAL
    thermostat.target_temperature = ON_TEMPERATURE

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    expect(state.state).to_equal(HVACMode.HEAT)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_be(None)
    expect(state.attributes.get(ATTR_PRESET_MODE)).to_equal(PRESET_ON)


@test
async def thermostat_set_preset_comfort(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    thermostat: MagicMock = Depends(thermostat_fx),
) -> None:
    """Set preset mode to comfort."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: PRESET_COMFORT},
        blocking=True,
    )
    cube.set_temperature_mode.assert_called_once_with(
        thermostat, thermostat.comfort_temperature, MAX_DEVICE_MODE_MANUAL
    )
    thermostat.mode = MAX_DEVICE_MODE_MANUAL
    thermostat.target_temperature = thermostat.comfort_temperature

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    expect(state.state).to_equal(HVACMode.HEAT)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(
        thermostat.comfort_temperature
    )
    expect(state.attributes.get(ATTR_PRESET_MODE)).to_equal(PRESET_COMFORT)


@test
async def thermostat_set_preset_eco(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    thermostat: MagicMock = Depends(thermostat_fx),
) -> None:
    """Set preset mode to eco."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: PRESET_ECO},
        blocking=True,
    )
    cube.set_temperature_mode.assert_called_once_with(
        thermostat, thermostat.eco_temperature, MAX_DEVICE_MODE_MANUAL
    )
    thermostat.mode = MAX_DEVICE_MODE_MANUAL
    thermostat.target_temperature = thermostat.eco_temperature

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    expect(state.state).to_equal(HVACMode.HEAT)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(thermostat.eco_temperature)
    expect(state.attributes.get(ATTR_PRESET_MODE)).to_equal(PRESET_ECO)


@test
async def thermostat_set_preset_away(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    thermostat: MagicMock = Depends(thermostat_fx),
) -> None:
    """Set preset mode to away."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: PRESET_AWAY},
        blocking=True,
    )
    cube.set_temperature_mode.assert_called_once_with(
        thermostat, None, MAX_DEVICE_MODE_VACATION
    )
    thermostat.mode = MAX_DEVICE_MODE_VACATION
    thermostat.target_temperature = thermostat.eco_temperature

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    expect(state.state).to_equal(HVACMode.HEAT)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(thermostat.eco_temperature)
    expect(state.attributes.get(ATTR_PRESET_MODE)).to_equal(PRESET_AWAY)


@test
async def thermostat_set_preset_boost(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    thermostat: MagicMock = Depends(thermostat_fx),
) -> None:
    """Set preset mode to boost."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: PRESET_BOOST},
        blocking=True,
    )
    cube.set_temperature_mode.assert_called_once_with(
        thermostat, None, MAX_DEVICE_MODE_BOOST
    )
    thermostat.mode = MAX_DEVICE_MODE_BOOST
    thermostat.target_temperature = thermostat.eco_temperature

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(ENTITY_ID)
    expect(state.state).to_equal(HVACMode.AUTO)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(thermostat.eco_temperature)
    expect(state.attributes.get(ATTR_PRESET_MODE)).to_equal(PRESET_BOOST)


@test
async def thermostat_set_preset_none(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    thermostat: MagicMock = Depends(thermostat_fx),
) -> None:
    """Set preset mode to none."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_PRESET_MODE,
        {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: PRESET_NONE},
        blocking=True,
    )
    cube.set_temperature_mode.assert_called_once_with(
        thermostat, None, MAX_DEVICE_MODE_AUTOMATIC
    )


@test
async def thermostat_set_invalid_preset(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    thermostat: MagicMock = Depends(thermostat_fx),
) -> None:
    """Set invalid preset mode."""
    async with expect_raises_async(ServiceValidationError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_PRESET_MODE,
            {ATTR_ENTITY_ID: ENTITY_ID, ATTR_PRESET_MODE: "invalid"},
            blocking=True,
        )
    cube.set_temperature_mode.assert_not_called()


@test
async def wallthermostat_set_hvac_mode_heat(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    wallthermostat: MagicMock = Depends(wallthermostat_fx),
) -> None:
    """Set wall thermostat hvac mode to heat."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: WALL_ENTITY_ID, ATTR_HVAC_MODE: HVACMode.HEAT},
        blocking=True,
    )
    cube.set_temperature_mode.assert_called_once_with(
        wallthermostat, MIN_TEMPERATURE, MAX_DEVICE_MODE_MANUAL
    )
    wallthermostat.target_temperature = MIN_TEMPERATURE

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(WALL_ENTITY_ID)
    expect(state.state).to_equal(HVACMode.HEAT)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(MIN_TEMPERATURE)


@test
async def wallthermostat_set_hvac_mode_auto(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    cube: MaxCube = Depends(cube_fx),
    wallthermostat: MagicMock = Depends(wallthermostat_fx),
) -> None:
    """Set wall thermostat hvac mode to auto."""
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {ATTR_ENTITY_ID: WALL_ENTITY_ID, ATTR_HVAC_MODE: HVACMode.AUTO},
        blocking=True,
    )
    cube.set_temperature_mode.assert_called_once_with(
        wallthermostat, None, MAX_DEVICE_MODE_AUTOMATIC
    )
    wallthermostat.mode = MAX_DEVICE_MODE_AUTOMATIC
    wallthermostat.target_temperature = 23.0

    async_fire_time_changed(hass, utcnow() + timedelta(minutes=5))
    await hass.async_block_till_done(wait_background_tasks=True)

    state = hass.states.get(WALL_ENTITY_ID)
    expect(state.state).to_equal(HVACMode.AUTO)
    expect(state.attributes.get(ATTR_TEMPERATURE)).to_equal(23.0)
