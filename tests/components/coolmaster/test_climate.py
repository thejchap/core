"""The test for the Coolmaster climate platform."""

from pycoolmasternet_async import SWING_MODES
from tryke import Depends, expect, fixture, test

from homeassistant.components.climate import (
    ATTR_CURRENT_TEMPERATURE,
    ATTR_FAN_MODE,
    ATTR_FAN_MODES,
    ATTR_HVAC_MODE,
    ATTR_HVAC_MODES,
    ATTR_SWING_MODE,
    ATTR_SWING_MODES,
    DOMAIN as CLIMATE_DOMAIN,
    FAN_HIGH,
    FAN_LOW,
    FAN_MEDIUM,
    SERVICE_SET_FAN_MODE,
    SERVICE_SET_HVAC_MODE,
    SERVICE_SET_SWING_MODE,
    SERVICE_SET_TEMPERATURE,
    ClimateEntityFeature,
    HVACMode,
)
from homeassistant.components.coolmaster.climate import FAN_MODES
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_FRIENDLY_NAME,
    ATTR_SUPPORTED_FEATURES,
    ATTR_TEMPERATURE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError

from ._fixtures import load_int, reset_warned_fan_speeds

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.hass_tryke_helpers import expect_raises_async


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor for tryke fixture resolution."""


@test
async def climate_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate state."""
    expect(hass.states.get("climate.l1_100").state).to_equal(HVACMode.OFF)
    expect(hass.states.get("climate.l1_101").state).to_equal(HVACMode.HEAT)
    expect(hass.states.get("climate.l1_102").state).to_equal(HVACMode.COOL)
    expect(hass.states.get("climate.l1_103").state).to_equal(HVACMode.COOL)
    expect(hass.states.get("climate.l1_104").state).to_equal(HVACMode.COOL)


@test
async def climate_friendly_name(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate friendly name."""
    expect(hass.states.get("climate.l1_100").attributes[ATTR_FRIENDLY_NAME]).to_equal(
        "L1.100"
    )
    expect(hass.states.get("climate.l1_101").attributes[ATTR_FRIENDLY_NAME]).to_equal(
        "L1.101"
    )
    expect(hass.states.get("climate.l1_102").attributes[ATTR_FRIENDLY_NAME]).to_equal(
        "L1.102"
    )
    expect(hass.states.get("climate.l1_103").attributes[ATTR_FRIENDLY_NAME]).to_equal(
        "L1.103"
    )
    expect(hass.states.get("climate.l1_104").attributes[ATTR_FRIENDLY_NAME]).to_equal(
        "L1.104"
    )


@test
async def climate_supported_features(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate supported features."""
    expect(
        hass.states.get("climate.l1_100").attributes[ATTR_SUPPORTED_FEATURES]
    ).to_equal(
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )
    expect(
        hass.states.get("climate.l1_101").attributes[ATTR_SUPPORTED_FEATURES]
    ).to_equal(
        ClimateEntityFeature.TARGET_TEMPERATURE
        | ClimateEntityFeature.FAN_MODE
        | ClimateEntityFeature.SWING_MODE
        | ClimateEntityFeature.TURN_OFF
        | ClimateEntityFeature.TURN_ON
    )


@test
async def climate_temperature(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate current temperature."""
    expect(
        hass.states.get("climate.l1_100").attributes[ATTR_CURRENT_TEMPERATURE]
    ).to_equal(25)
    expect(
        hass.states.get("climate.l1_101").attributes[ATTR_CURRENT_TEMPERATURE]
    ).to_equal(10)
    expect(
        hass.states.get("climate.l1_102").attributes[ATTR_CURRENT_TEMPERATURE]
    ).to_equal(25)
    expect(
        hass.states.get("climate.l1_103").attributes[ATTR_CURRENT_TEMPERATURE]
    ).to_equal(25)
    expect(
        hass.states.get("climate.l1_104").attributes[ATTR_CURRENT_TEMPERATURE]
    ).to_equal(25)


@test
async def climate_thermostat(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate thermostat."""
    expect(hass.states.get("climate.l1_100").attributes[ATTR_TEMPERATURE]).to_equal(20)
    expect(hass.states.get("climate.l1_101").attributes[ATTR_TEMPERATURE]).to_equal(20)
    expect(hass.states.get("climate.l1_102").attributes[ATTR_TEMPERATURE]).to_equal(20)
    expect(hass.states.get("climate.l1_103").attributes[ATTR_TEMPERATURE]).to_equal(25)
    expect(hass.states.get("climate.l1_104").attributes[ATTR_TEMPERATURE]).to_equal(25)


@test
async def climate_hvac_modes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate hvac modes."""
    expect(hass.states.get("climate.l1_100").attributes[ATTR_HVAC_MODES]).to_equal(
        [
            HVACMode.OFF,
            HVACMode.COOL,
            HVACMode.HEAT,
        ]
    )
    for unit in (
        "climate.l1_101",
        "climate.l1_102",
        "climate.l1_103",
        "climate.l1_104",
    ):
        expect(hass.states.get(unit).attributes[ATTR_HVAC_MODES]).to_equal(
            hass.states.get("climate.l1_100").attributes[ATTR_HVAC_MODES]
        )


@test
async def climate_fan_mode(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate fan mode."""
    expect(hass.states.get("climate.l1_100").attributes[ATTR_FAN_MODE]).to_equal(
        FAN_LOW
    )
    expect(hass.states.get("climate.l1_101").attributes[ATTR_FAN_MODE]).to_equal(
        FAN_HIGH
    )
    expect(hass.states.get("climate.l1_102").attributes[ATTR_FAN_MODE]).to_equal("vlow")
    expect(hass.states.get("climate.l1_103").attributes[ATTR_FAN_MODE]).to_equal(
        FAN_MEDIUM
    )
    expect(hass.states.get("climate.l1_104").attributes[ATTR_FAN_MODE]).to_equal(
        "ultra"
    )


@test
async def climate_unknown_fan_mode_warning(
    caplog: LogCapture = Depends(caplog_fixture),
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate unknown fan mode warning."""
    # TODO(2026.7.0): When support for unknown fan speeds is removed, delete this test.
    setup_logs = caplog.get_records(when="setup")

    # Assert that both unknown fan speeds logged a warning.
    expect(
        any(
            "Detected unknown fan speed value from HVAC unit: ultra. "
            "Support for unknown fan speeds will be removed in 2026.7.0"
            in rec.getMessage()
            and rec.levelname == "WARNING"
            for rec in setup_logs
        )
    ).to_be(True)
    expect(
        any(
            "Detected unknown fan speed value from HVAC unit: vlow. "
            "Support for unknown fan speeds will be removed in 2026.7.0"
            in rec.getMessage()
            and rec.levelname == "WARNING"
            for rec in setup_logs
        )
    ).to_be(True)

    start_record_count = len(caplog.records)
    climate_component = hass.data[CLIMATE_DOMAIN]
    entity = climate_component.get_entity("climate.l1_104")

    # Access the fan_mode property again to ensure no duplicate warnings are logged
    expect(entity.fan_mode).to_equal("ultra")
    end_record_count = len(caplog.records)

    for record in caplog.records[start_record_count:end_record_count]:
        expect(
            "Detected unknown fan speed value from HVAC unit: ultra. "
            "Support for unknown fan speeds will be removed in 2026.7.0"
            in record.getMessage()
            and record.levelname == "WARNING"
        ).to_be(False)


@test
async def climate_fan_modes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate fan modes."""
    expect(hass.states.get("climate.l1_100").attributes[ATTR_FAN_MODES]).to_equal(
        FAN_MODES
    )
    for unit in (
        "climate.l1_101",
        "climate.l1_102",
        "climate.l1_103",
        "climate.l1_104",
    ):
        expect(hass.states.get(unit).attributes[ATTR_FAN_MODES]).to_equal(
            hass.states.get("climate.l1_100").attributes[ATTR_FAN_MODES]
        )


@test
async def climate_swing_mode(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate swing mode."""
    expect(ATTR_SWING_MODE not in hass.states.get("climate.l1_100").attributes).to_be(
        True
    )
    expect(hass.states.get("climate.l1_101").attributes[ATTR_SWING_MODE]).to_equal(
        "horizontal"
    )


@test
async def climate_swing_modes(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate swing modes."""
    expect(ATTR_SWING_MODES not in hass.states.get("climate.l1_100").attributes).to_be(
        True
    )
    expect(hass.states.get("climate.l1_101").attributes[ATTR_SWING_MODES]).to_equal(
        SWING_MODES
    )


@test
async def set_temperature(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate set temperature."""
    expect(hass.states.get("climate.l1_100").attributes[ATTR_TEMPERATURE]).to_equal(20)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_TEMPERATURE,
        {
            ATTR_ENTITY_ID: "climate.l1_100",
            ATTR_TEMPERATURE: 30,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(hass.states.get("climate.l1_100").attributes[ATTR_TEMPERATURE]).to_equal(30)


@test.cases(
    test.case("low", target_fan_mode=FAN_LOW),
    test.case("medium", target_fan_mode=FAN_MEDIUM),
    test.case("high", target_fan_mode=FAN_HIGH),
    test.case("auto", target_fan_mode="auto"),
)
async def set_fan_mode(
    target_fan_mode: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate set fan mode."""
    expect(hass.states.get("climate.l1_100").attributes[ATTR_FAN_MODE]).to_equal(
        FAN_LOW
    )

    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_FAN_MODE,
        {
            ATTR_ENTITY_ID: "climate.l1_100",
            ATTR_FAN_MODE: target_fan_mode,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(hass.states.get("climate.l1_100").attributes[ATTR_FAN_MODE]).to_equal(
        target_fan_mode
    )


@test
async def set_swing_mode(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate set swing mode."""
    expect(hass.states.get("climate.l1_101").attributes[ATTR_SWING_MODE]).to_equal(
        "horizontal"
    )
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_SWING_MODE,
        {
            ATTR_ENTITY_ID: "climate.l1_101",
            ATTR_SWING_MODE: "vertical",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(hass.states.get("climate.l1_101").attributes[ATTR_SWING_MODE]).to_equal(
        "vertical"
    )


@test
async def set_swing_mode_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate set swing mode with error."""
    async with expect_raises_async(HomeAssistantError):
        await hass.services.async_call(
            CLIMATE_DOMAIN,
            SERVICE_SET_SWING_MODE,
            {
                ATTR_ENTITY_ID: "climate.l1_101",
                ATTR_SWING_MODE: "",
            },
            blocking=True,
        )


@test
async def set_hvac_mode(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate set hvac mode."""
    expect(hass.states.get("climate.l1_100").state).to_equal(HVACMode.OFF)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {
            ATTR_ENTITY_ID: "climate.l1_100",
            ATTR_HVAC_MODE: HVACMode.HEAT,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(hass.states.get("climate.l1_100").state).to_equal(HVACMode.HEAT)


@test
async def set_hvac_mode_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate set hvac mode to off."""
    expect(hass.states.get("climate.l1_101").state).to_equal(HVACMode.HEAT)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_SET_HVAC_MODE,
        {
            ATTR_ENTITY_ID: "climate.l1_101",
            ATTR_HVAC_MODE: HVACMode.OFF,
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(hass.states.get("climate.l1_101").state).to_equal(HVACMode.OFF)


@test
async def turn_on(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate turn on."""
    expect(hass.states.get("climate.l1_100").state).to_equal(HVACMode.OFF)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_ON,
        {
            ATTR_ENTITY_ID: "climate.l1_100",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(hass.states.get("climate.l1_100").state).to_equal(HVACMode.COOL)


@test
async def turn_off(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _load: MockConfigEntry = Depends(load_int),
) -> None:
    """Test the Coolmaster climate turn off."""
    expect(hass.states.get("climate.l1_101").state).to_equal(HVACMode.HEAT)
    await hass.services.async_call(
        CLIMATE_DOMAIN,
        SERVICE_TURN_OFF,
        {
            ATTR_ENTITY_ID: "climate.l1_101",
        },
        blocking=True,
    )
    await hass.async_block_till_done()
    expect(hass.states.get("climate.l1_101").state).to_equal(HVACMode.OFF)


_ = (load_int, reset_warned_fan_speeds)
