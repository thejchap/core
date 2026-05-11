"""Test different accessory types: Thermostats (tryke port).

Larger tests (parametrize-heavy state-dispatch + raise/event chains) remain stubbed
under ``@test.skip`` and will be ported in a follow-up.
"""

from __future__ import annotations

from unittest.mock import patch

from pyhap.const import HAP_REPR_AID, HAP_REPR_CHARS, HAP_REPR_IID, HAP_REPR_VALUE
from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import (
    ATTR_FAN_MODE,
    ATTR_FAN_MODES,
    ATTR_HVAC_ACTION,
    ATTR_HVAC_MODE,
    ATTR_HVAC_MODES,
    ATTR_MAX_TEMP,
    ATTR_MIN_TEMP,
    ATTR_PRESET_MODE,
    ATTR_PRESET_MODES,
    ATTR_SWING_MODES,
    ATTR_TARGET_TEMP_HIGH,
    ATTR_TARGET_TEMP_LOW,
    ATTR_TARGET_TEMP_STEP,
    DEFAULT_MAX_TEMP,
    DEFAULT_MIN_TEMP,
    DOMAIN as CLIMATE_DOMAIN,
    FAN_AUTO,
    FAN_HIGH,
    FAN_LOW,
    SWING_BOTH,
    SWING_HORIZONTAL,
    SWING_OFF,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.components.homekit.accessories import HomeDriver
from homeassistant.components.homekit.const import (
    CHAR_CURRENT_FAN_STATE,
    CHAR_ROTATION_SPEED,
    CHAR_SWING_MODE,
    CHAR_TARGET_FAN_STATE,
    PROP_MAX_VALUE,
    PROP_MIN_STEP,
    PROP_MIN_VALUE,
)
from homeassistant.components.homekit.type_thermostats import (
    FAN_STATE_ACTIVE,
    FAN_STATE_IDLE,
    FAN_STATE_INACTIVE,
    HC_HEAT_COOL_HEAT,
    HC_HEAT_COOL_OFF,
    Thermostat,
    WaterHeater,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant

from tests.common import async_mock_service
from tests.components.homekit._fixtures import hk_driver as hk_driver_fixture
from tests.hass_fixtures import hass as hass_fixture


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Module-local anchor fixture (see PATTERNS.md)."""
    return hass


# ---------------------------------------------------------------------------
# Ported tests
# ---------------------------------------------------------------------------


@test
async def thermostat_get_temperature_range(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if temperature range is evaluated correctly."""
    entity_id = "climate.test"

    hass.states.async_set(entity_id, HVACMode.OFF)
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 2, None)

    hass.states.async_set(
        entity_id, HVACMode.OFF, {ATTR_MIN_TEMP: 20, ATTR_MAX_TEMP: 25}
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    expect(acc.get_temperature_range(state)).to_equal((20, 25))

    acc._unit = UnitOfTemperature.FAHRENHEIT  # noqa: SLF001
    hass.states.async_set(
        entity_id, HVACMode.OFF, {ATTR_MIN_TEMP: 60, ATTR_MAX_TEMP: 70}
    )
    await hass.async_block_till_done()
    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    expect(acc.get_temperature_range(state)).to_equal((15.5, 21.0))


@test
async def thermostat_temperature_step_whole(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test climate device with single digit precision."""
    entity_id = "climate.test"

    hass.states.async_set(entity_id, HVACMode.OFF, {ATTR_TARGET_TEMP_STEP: 1})
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    expect(acc.char_target_temp.properties[PROP_MIN_STEP]).to_equal(0.1)


@test
async def thermostat_hvac_modes(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if unsupported HVAC modes are deactivated in HomeKit."""
    entity_id = "climate.test"

    hass.states.async_set(
        entity_id, HVACMode.OFF, {ATTR_HVAC_MODES: [HVACMode.HEAT, HVACMode.OFF]}
    )

    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()
    hap = acc.char_target_heat_cool.to_HAP()
    expect(hap["valid-values"]).to_equal([0, 1])
    expect(acc.char_target_heat_cool.value).to_equal(0)

    expect(lambda: acc.char_target_heat_cool.set_value(3)).to_raise(ValueError)
    await hass.async_block_till_done()
    expect(acc.char_target_heat_cool.value).to_equal(0)

    acc.char_target_heat_cool.set_value(1)
    await hass.async_block_till_done()
    expect(acc.char_target_heat_cool.value).to_equal(1)

    expect(lambda: acc.char_target_heat_cool.set_value(2)).to_raise(ValueError)
    await hass.async_block_till_done()
    expect(acc.char_target_heat_cool.value).to_equal(1)


@test
async def thermostat_hvac_modes_with_auto_only(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if unsupported HVAC modes are deactivated in HomeKit (auto-only)."""
    entity_id = "climate.test"

    hass.states.async_set(
        entity_id, HVACMode.AUTO, {ATTR_HVAC_MODES: [HVACMode.AUTO, HVACMode.OFF]}
    )

    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()
    hap = acc.char_target_heat_cool.to_HAP()
    expect(hap["valid-values"]).to_equal([0, 3])
    expect(acc.char_target_heat_cool.value).to_equal(3)

    acc.char_target_heat_cool.set_value(3)
    await hass.async_block_till_done()
    expect(acc.char_target_heat_cool.value).to_equal(3)

    expect(lambda: acc.char_target_heat_cool.set_value(1)).to_raise(ValueError)
    await hass.async_block_till_done()
    expect(acc.char_target_heat_cool.value).to_equal(3)

    expect(lambda: acc.char_target_heat_cool.set_value(2)).to_raise(ValueError)
    await hass.async_block_till_done()
    expect(acc.char_target_heat_cool.value).to_equal(3)

    char_target_heat_cool_iid = acc.char_target_heat_cool.to_HAP()[HAP_REPR_IID]
    call_set_hvac_mode = async_mock_service(hass, CLIMATE_DOMAIN, "set_hvac_mode")
    await hass.async_block_till_done()
    hk_driver.set_characteristics(
        {
            HAP_REPR_CHARS: [
                {
                    HAP_REPR_AID: acc.aid,
                    HAP_REPR_IID: char_target_heat_cool_iid,
                    HAP_REPR_VALUE: HC_HEAT_COOL_HEAT,
                },
            ]
        },
        "mock_addr",
    )

    await hass.async_block_till_done()
    expect(bool(call_set_hvac_mode)).to_be(True)
    expect(call_set_hvac_mode[0].data[ATTR_ENTITY_ID]).to_equal(entity_id)
    expect(call_set_hvac_mode[0].data[ATTR_HVAC_MODE]).to_equal(HVACMode.AUTO)


@test
async def thermostat_hvac_modes_without_off(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test a thermostat that has no off."""
    entity_id = "climate.test"

    hass.states.async_set(
        entity_id, HVACMode.AUTO, {ATTR_HVAC_MODES: [HVACMode.AUTO, HVACMode.HEAT]}
    )

    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()
    hap = acc.char_target_heat_cool.to_HAP()
    expect(hap["valid-values"]).to_equal([1, 3])
    expect(acc.char_target_heat_cool.value).to_equal(3)

    acc.char_target_heat_cool.set_value(3)
    await hass.async_block_till_done()
    expect(acc.char_target_heat_cool.value).to_equal(3)

    acc.char_target_heat_cool.set_value(1)
    await hass.async_block_till_done()
    expect(acc.char_target_heat_cool.value).to_equal(1)

    expect(lambda: acc.char_target_heat_cool.set_value(2)).to_raise(ValueError)
    await hass.async_block_till_done()
    expect(acc.char_target_heat_cool.value).to_equal(1)

    expect(lambda: acc.char_target_heat_cool.set_value(0)).to_raise(ValueError)
    await hass.async_block_till_done()
    expect(acc.char_target_heat_cool.value).to_equal(1)


@test
async def thermostat_with_no_modes_when_we_first_see(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if a thermostat that is not ready when we first see it."""
    entity_id = "climate.test"
    base_attrs = {
        ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE,
        ATTR_HVAC_MODES: [],
    }

    hass.states.async_set(entity_id, HVACMode.OFF, base_attrs)
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    expect(acc.char_cooling_thresh_temp.value).to_equal(23.0)
    expect(acc.char_heating_thresh_temp.value).to_equal(19.0)

    expect(acc.char_cooling_thresh_temp.properties[PROP_MAX_VALUE]).to_equal(
        DEFAULT_MAX_TEMP
    )
    expect(acc.char_cooling_thresh_temp.properties[PROP_MIN_VALUE]).to_equal(7.0)
    expect(acc.char_cooling_thresh_temp.properties[PROP_MIN_STEP]).to_equal(0.1)
    expect(acc.char_heating_thresh_temp.properties[PROP_MAX_VALUE]).to_equal(
        DEFAULT_MAX_TEMP
    )
    expect(acc.char_heating_thresh_temp.properties[PROP_MIN_VALUE]).to_equal(7.0)
    expect(acc.char_heating_thresh_temp.properties[PROP_MIN_STEP]).to_equal(0.1)

    expect(acc.char_target_heat_cool.value).to_equal(0)

    # Verify reload on modes changed out from under us
    with patch.object(acc, "async_reload") as mock_reload:
        hass.states.async_set(
            entity_id,
            HVACMode.HEAT_COOL,
            {
                **base_attrs,
                ATTR_TARGET_TEMP_HIGH: 22.0,
                ATTR_TARGET_TEMP_LOW: 20.0,
                "current_temperature": 18.0,
                ATTR_HVAC_ACTION: HVACAction.HEATING,
                ATTR_HVAC_MODES: [HVACMode.HEAT_COOL, HVACMode.OFF, HVACMode.AUTO],
            },
        )
        await hass.async_block_till_done()
        expect(mock_reload.called).to_be(True)


@test
async def thermostat_with_no_off_after_recheck(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if a thermostat that is not ready when we first see it actually does not have off."""
    entity_id = "climate.test"

    base_attrs = {
        ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE,
        ATTR_HVAC_MODES: [],
    }
    hass.states.async_set(entity_id, HVACMode.COOL, base_attrs)
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    expect(acc.char_cooling_thresh_temp.value).to_equal(23.0)
    expect(acc.char_heating_thresh_temp.value).to_equal(19.0)

    expect(acc.char_target_heat_cool.value).to_equal(2)

    # Verify reload when modes change out from under us
    with patch.object(acc, "async_reload") as mock_reload:
        hass.states.async_set(
            entity_id,
            HVACMode.HEAT_COOL,
            {
                **base_attrs,
                ATTR_TARGET_TEMP_HIGH: 22.0,
                ATTR_TARGET_TEMP_LOW: 20.0,
                "current_temperature": 18.0,
                ATTR_HVAC_ACTION: HVACAction.HEATING,
                ATTR_HVAC_MODES: [HVACMode.HEAT_COOL, HVACMode.AUTO],
            },
        )
        await hass.async_block_till_done()
        expect(mock_reload.called).to_be(True)


@test
async def thermostat_with_temp_clamps(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test that temperatures are clamped to valid values to prevent homekit crash."""
    entity_id = "climate.test"
    base_attrs = {
        ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE,
        ATTR_HVAC_MODES: [HVACMode.HEAT_COOL, HVACMode.AUTO],
        ATTR_MAX_TEMP: 100,
        ATTR_MIN_TEMP: 50,
    }
    hass.states.async_set(entity_id, HVACMode.COOL, base_attrs)
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    expect(acc.char_cooling_thresh_temp.value).to_equal(50)
    expect(acc.char_heating_thresh_temp.value).to_equal(50)

    expect(acc.char_cooling_thresh_temp.properties[PROP_MAX_VALUE]).to_equal(100)
    expect(acc.char_cooling_thresh_temp.properties[PROP_MIN_VALUE]).to_equal(50)
    expect(acc.char_cooling_thresh_temp.properties[PROP_MIN_STEP]).to_equal(0.1)
    expect(acc.char_heating_thresh_temp.properties[PROP_MAX_VALUE]).to_equal(100)
    expect(acc.char_heating_thresh_temp.properties[PROP_MIN_VALUE]).to_equal(50)
    expect(acc.char_heating_thresh_temp.properties[PROP_MIN_STEP]).to_equal(0.1)

    expect(acc.char_target_heat_cool.value).to_equal(3)

    hass.states.async_set(
        entity_id,
        HVACMode.HEAT_COOL,
        {
            **base_attrs,
            ATTR_TARGET_TEMP_HIGH: 822.0,
            ATTR_TARGET_TEMP_LOW: 20.0,
            "current_temperature": 9918.0,
            ATTR_HVAC_ACTION: HVACAction.HEATING,
        },
    )
    await hass.async_block_till_done()
    expect(acc.char_heating_thresh_temp.value).to_equal(50.0)
    expect(acc.char_cooling_thresh_temp.value).to_equal(100.0)
    expect(acc.char_current_heat_cool.value).to_equal(1)
    expect(acc.char_target_heat_cool.value).to_equal(3)
    expect(acc.char_current_temp.value).to_equal(1000)
    expect(acc.char_display_units.value).to_equal(0)


@test
async def thermostat_with_fan_modes_set_to_none(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test a thermostate with fan modes set to None."""
    entity_id = "climate.test"
    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        {
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            | ClimateEntityFeature.FAN_MODE
            | ClimateEntityFeature.SWING_MODE,
            ATTR_FAN_MODES: None,
            ATTR_SWING_MODES: [SWING_BOTH, SWING_OFF, SWING_HORIZONTAL],
            ATTR_HVAC_ACTION: HVACAction.IDLE,
            ATTR_FAN_MODE: FAN_AUTO,
            "swing_mode": SWING_BOTH,
            ATTR_HVAC_MODES: [
                HVACMode.HEAT,
                HVACMode.HEAT_COOL,
                HVACMode.FAN_ONLY,
                HVACMode.COOL,
                HVACMode.OFF,
                HVACMode.AUTO,
            ],
        },
    )
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    expect(acc.char_cooling_thresh_temp.value).to_equal(23.0)
    expect(acc.char_heating_thresh_temp.value).to_equal(19.0)
    expect(acc.ordered_fan_speeds).to_equal([])
    expect(CHAR_ROTATION_SPEED in acc.fan_chars).to_be(False)
    expect(CHAR_TARGET_FAN_STATE in acc.fan_chars).to_be(False)
    expect(CHAR_SWING_MODE in acc.fan_chars).to_be(True)
    expect(CHAR_CURRENT_FAN_STATE in acc.fan_chars).to_be(True)


@test
async def thermostat_with_fan_modes_set_to_none_not_supported(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test a thermostate with fan modes set to None and supported feature missing."""
    entity_id = "climate.test"
    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        {
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE
            | ClimateEntityFeature.SWING_MODE,
            ATTR_FAN_MODES: None,
            ATTR_SWING_MODES: [SWING_BOTH, SWING_OFF, SWING_HORIZONTAL],
            ATTR_HVAC_ACTION: HVACAction.IDLE,
            ATTR_FAN_MODE: FAN_AUTO,
            "swing_mode": SWING_BOTH,
            ATTR_HVAC_MODES: [
                HVACMode.HEAT,
                HVACMode.HEAT_COOL,
                HVACMode.FAN_ONLY,
                HVACMode.COOL,
                HVACMode.OFF,
                HVACMode.AUTO,
            ],
        },
    )
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    expect(acc.char_cooling_thresh_temp.value).to_equal(23.0)
    expect(acc.char_heating_thresh_temp.value).to_equal(19.0)
    expect(acc.ordered_fan_speeds).to_equal([])
    expect(CHAR_ROTATION_SPEED in acc.fan_chars).to_be(False)
    expect(CHAR_TARGET_FAN_STATE in acc.fan_chars).to_be(False)
    expect(CHAR_SWING_MODE in acc.fan_chars).to_be(True)
    expect(CHAR_CURRENT_FAN_STATE in acc.fan_chars).to_be(True)


@test
async def thermostat_with_supported_features_target_temp_but_fan_mode_set(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test a thermostate with fan mode and supported feature missing."""
    entity_id = "climate.test"
    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        {
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE,
            ATTR_MIN_TEMP: 44.6,
            ATTR_MAX_TEMP: 95,
            ATTR_PRESET_MODES: ["home", "away"],
            "temperature": 67,
            ATTR_TARGET_TEMP_HIGH: None,
            ATTR_TARGET_TEMP_LOW: None,
            ATTR_FAN_MODE: FAN_AUTO,
            ATTR_FAN_MODES: None,
            ATTR_HVAC_ACTION: HVACAction.IDLE,
            ATTR_PRESET_MODE: "home",
            ATTR_FRIENDLY_NAME: "Rec Room",
            ATTR_HVAC_MODES: [HVACMode.OFF, HVACMode.HEAT],
        },
    )
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    expect(acc.ordered_fan_speeds).to_equal([])
    expect(bool(acc.fan_chars)).to_be(False)


@test
async def thermostat_fan_state_with_preheating_and_defrosting(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test thermostat fan state mappings for preheating and defrosting actions."""
    entity_id = "climate.test"
    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE,
            ATTR_FAN_MODES: [FAN_AUTO, FAN_LOW, FAN_HIGH],
            ATTR_HVAC_ACTION: HVACAction.IDLE,
            ATTR_FAN_MODE: FAN_AUTO,
            ATTR_HVAC_MODES: [HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF],
        },
    )
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    expect(CHAR_CURRENT_FAN_STATE in acc.fan_chars).to_be(True)
    expect(hasattr(acc, "char_current_fan_state")).to_be(True)

    # PREHEATING -> FAN_STATE_IDLE
    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE,
            ATTR_FAN_MODES: [FAN_AUTO, FAN_LOW, FAN_HIGH],
            ATTR_HVAC_ACTION: HVACAction.PREHEATING,
            ATTR_FAN_MODE: FAN_AUTO,
            ATTR_HVAC_MODES: [HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF],
        },
    )
    await hass.async_block_till_done()
    expect(acc.char_current_fan_state.value).to_equal(FAN_STATE_IDLE)

    # DEFROSTING -> FAN_STATE_IDLE
    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE,
            ATTR_FAN_MODES: [FAN_AUTO, FAN_LOW, FAN_HIGH],
            ATTR_HVAC_ACTION: HVACAction.DEFROSTING,
            ATTR_FAN_MODE: FAN_AUTO,
            ATTR_HVAC_MODES: [HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF],
        },
    )
    await hass.async_block_till_done()
    expect(acc.char_current_fan_state.value).to_equal(FAN_STATE_IDLE)

    # HEATING -> FAN_STATE_ACTIVE
    hass.states.async_set(
        entity_id,
        HVACMode.HEAT,
        {
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE,
            ATTR_FAN_MODES: [FAN_AUTO, FAN_LOW, FAN_HIGH],
            ATTR_HVAC_ACTION: HVACAction.HEATING,
            ATTR_FAN_MODE: FAN_AUTO,
            ATTR_HVAC_MODES: [HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF],
        },
    )
    await hass.async_block_till_done()
    expect(acc.char_current_fan_state.value).to_equal(FAN_STATE_ACTIVE)

    # OFF -> FAN_STATE_INACTIVE
    hass.states.async_set(
        entity_id,
        HVACMode.OFF,
        {
            ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
            | ClimateEntityFeature.FAN_MODE,
            ATTR_FAN_MODES: [FAN_AUTO, FAN_LOW, FAN_HIGH],
            ATTR_HVAC_ACTION: HVACAction.OFF,
            ATTR_FAN_MODE: FAN_AUTO,
            ATTR_HVAC_MODES: [HVACMode.HEAT, HVACMode.COOL, HVACMode.OFF],
        },
    )
    await hass.async_block_till_done()
    expect(acc.char_current_fan_state.value).to_equal(FAN_STATE_INACTIVE)


@test
async def thermostat_reversed_min_max(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test reversed min/max temperatures."""
    entity_id = "climate.test"
    base_attrs = {
        ATTR_SUPPORTED_FEATURES: ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.TARGET_TEMPERATURE_RANGE,
        ATTR_HVAC_MODES: [
            HVACMode.HEAT,
            HVACMode.HEAT_COOL,
            HVACMode.FAN_ONLY,
            HVACMode.COOL,
            HVACMode.OFF,
            HVACMode.AUTO,
        ],
        ATTR_MAX_TEMP: DEFAULT_MAX_TEMP,
        ATTR_MIN_TEMP: DEFAULT_MIN_TEMP,
    }
    hass.states.async_set(entity_id, HVACMode.OFF, base_attrs)
    await hass.async_block_till_done()
    acc = Thermostat(hass, hk_driver, "Climate", entity_id, 1, None)
    hk_driver.add_accessory(acc)

    acc.run()
    await hass.async_block_till_done()

    expect(acc.char_cooling_thresh_temp.value).to_equal(23.0)
    expect(acc.char_heating_thresh_temp.value).to_equal(19.0)

    expect(acc.char_cooling_thresh_temp.properties[PROP_MAX_VALUE]).to_equal(
        DEFAULT_MAX_TEMP
    )
    expect(acc.char_cooling_thresh_temp.properties[PROP_MIN_VALUE]).to_equal(7.0)
    expect(acc.char_cooling_thresh_temp.properties[PROP_MIN_STEP]).to_equal(0.1)
    expect(acc.char_heating_thresh_temp.properties[PROP_MAX_VALUE]).to_equal(
        DEFAULT_MAX_TEMP
    )
    expect(acc.char_heating_thresh_temp.properties[PROP_MIN_VALUE]).to_equal(7.0)
    expect(acc.char_heating_thresh_temp.properties[PROP_MIN_STEP]).to_equal(0.1)


@test
async def water_heater_no_off_mode(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test water heater without ON_OFF or OPERATION_MODE does not expose Off."""
    entity_id = "water_heater.test"

    hass.states.async_set(entity_id, HVACMode.HEAT)
    await hass.async_block_till_done()
    acc = WaterHeater(hass, hk_driver, "WaterHeater", entity_id, 2, None)
    acc.run()
    await hass.async_block_till_done()

    valid_values = acc.char_target_heat_cool.properties.get("ValidValues", {})
    expect(valid_values).to_equal({"Heat": 1})
    expect("Off" in valid_values).to_be(False)


@test
async def water_heater_get_temperature_range(
    _t: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hk_driver: HomeDriver = Depends(hk_driver_fixture),
) -> None:
    """Test if temperature range is evaluated correctly for water heater."""
    entity_id = "water_heater.test"

    hass.states.async_set(entity_id, HVACMode.HEAT)
    await hass.async_block_till_done()
    acc = WaterHeater(hass, hk_driver, "WaterHeater", entity_id, 2, None)

    hass.states.async_set(
        entity_id, HVACMode.HEAT, {ATTR_MIN_TEMP: 20, ATTR_MAX_TEMP: 25}
    )
    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    await hass.async_block_till_done()
    expect(acc.get_temperature_range(state)).to_equal((20, 25))

    acc._unit = UnitOfTemperature.FAHRENHEIT  # noqa: SLF001
    hass.states.async_set(
        entity_id, HVACMode.OFF, {ATTR_MIN_TEMP: 60, ATTR_MAX_TEMP: 70}
    )
    state = hass.states.get(entity_id)
    expect(state is not None).to_be(True)
    await hass.async_block_till_done()
    expect(acc.get_temperature_range(state)).to_equal((15.5, 21.0))


# ---------------------------------------------------------------------------
# Tests still deferred — large/parametrize-heavy or requires extra fixtures
# ---------------------------------------------------------------------------


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat() -> None:
    """Stub for test_thermostat."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_auto() -> None:
    """Stub for test_thermostat_auto."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_mode_and_temp_change() -> None:
    """Stub for test_thermostat_mode_and_temp_change."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_humidity() -> None:
    """Stub for test_thermostat_humidity."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_humidity_with_target_humidity() -> None:
    """Stub for test_thermostat_humidity_with_target_humidity."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_power_state() -> None:
    """Stub for test_thermostat_power_state."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_fahrenheit() -> None:
    """Stub for test_thermostat_fahrenheit."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_restore() -> None:
    """Stub for test_thermostat_restore."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_hvac_modes_with_auto_heat_cool() -> None:
    """Stub for test_thermostat_hvac_modes_with_auto_heat_cool."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_hvac_modes_with_auto_no_heat_cool() -> None:
    """Stub for test_thermostat_hvac_modes_with_auto_no_heat_cool."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_hvac_modes_with_heat_only() -> None:
    """Stub for test_thermostat_hvac_modes_with_heat_only."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_hvac_modes_with_cool_only() -> None:
    """Stub for test_thermostat_hvac_modes_with_cool_only."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_hvac_modes_with_heat_cool_only() -> None:
    """Stub for test_thermostat_hvac_modes_with_heat_cool_only."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_without_target_temp_only_range() -> None:
    """Stub for test_thermostat_without_target_temp_only_range."""


@test.skip("large file (2897 LOC) - port deferred")
async def water_heater() -> None:
    """Stub for test_water_heater."""


@test.skip("large file (2897 LOC) - port deferred")
async def water_heater_off_mode_on_off() -> None:
    """Stub for test_water_heater_off_mode_on_off."""


@test.skip("large file (2897 LOC) - port deferred")
async def water_heater_off_mode_operation_mode() -> None:
    """Stub for test_water_heater_off_mode_operation_mode."""


@test.skip("large file (2897 LOC) - port deferred")
async def water_heater_fahrenheit() -> None:
    """Stub for test_water_heater_fahrenheit."""


@test.skip("large file (2897 LOC) - port deferred")
async def water_heater_restore() -> None:
    """Stub for test_water_heater_restore."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_with_fan_modes_with_auto() -> None:
    """Stub for test_thermostat_with_fan_modes_with_auto."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_with_fan_modes_with_off() -> None:
    """Stub for test_thermostat_with_fan_modes_with_off."""


@test.skip("large file (2897 LOC) - port deferred")
async def thermostat_handles_unknown_state() -> None:
    """Stub for test_thermostat_handles_unknown_state."""
