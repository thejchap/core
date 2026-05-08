"""Test KNX climate."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.knx.schema import ClimateSchema
from homeassistant.const import CONF_NAME
from homeassistant.core import HomeAssistant

from .conftest import KNXTestKit
from ._fixtures import knx, mock_config_entry

from tests.common import async_capture_events
from tests.hass_fixtures import hass as hass_fixture, mock_network

RAW_FLOAT_20_0 = (0x07, 0xD0)
RAW_FLOAT_21_0 = (0x0C, 0x1A)
RAW_FLOAT_22_0 = (0x0C, 0x4C)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def climate_basic_temperature_set(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    knx: KNXTestKit = Depends(knx),
) -> None:
    """Test KNX climate basic temperature set."""
    await knx.setup_integration(
        {
            ClimateSchema.PLATFORM: {
                CONF_NAME: "test",
                ClimateSchema.CONF_TEMPERATURE_ADDRESS: "1/2/3",
                ClimateSchema.CONF_TARGET_TEMPERATURE_ADDRESS: "1/2/4",
                ClimateSchema.CONF_TARGET_TEMPERATURE_STATE_ADDRESS: "1/2/5",
            }
        }
    )
    events = async_capture_events(hass, "state_changed")

    await knx.assert_read("1/2/3")
    await knx.assert_read("1/2/5")
    await knx.receive_response("1/2/3", RAW_FLOAT_21_0)
    await knx.receive_response("1/2/5", RAW_FLOAT_22_0)
    events.clear()

    await hass.services.async_call(
        "climate",
        "set_temperature",
        {"entity_id": "climate.test", "temperature": 20},
        blocking=True,
    )
    await knx.assert_write("1/2/4", RAW_FLOAT_20_0)
    expect(len(events)).to_equal(1)


@test.skip("port deferred - sibling test")
async def climate_on_off() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def climate_hvac_mode() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def climate_heat_cool_read_only() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def climate_heat_cool_read_only_on_off() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def climate_preset_mode() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def update_entity() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def command_value_idle_mode() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def fan_speed_3_steps() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def fan_speed_2_steps() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def fan_speed_1_step() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def fan_speed_5_steps() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def fan_speed_percentage() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def fan_speed_percentage_4_steps() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def fan_speed_zero_mode_auto() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def climate_humidity() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def swing() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def horizontal_swing() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def climate_ui_create() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def climate_ui_load() -> None:
    """Stub."""
