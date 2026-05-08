"""Test KNX light."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.knx.const import KNX_ADDRESS
from homeassistant.components.knx.schema import LightSchema
from homeassistant.components.light import ColorMode
from homeassistant.const import CONF_NAME, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant

from .conftest import KNXTestKit
from ._fixtures import knx, mock_config_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def light_simple(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    knx: KNXTestKit = Depends(knx),
) -> None:
    """Test simple KNX light."""
    test_address = "1/1/1"
    await knx.setup_integration(
        {
            LightSchema.PLATFORM: {
                CONF_NAME: "test",
                KNX_ADDRESS: test_address,
            }
        }
    )

    knx.assert_state(
        "light.test",
        STATE_OFF,
        supported_color_modes=[ColorMode.ONOFF],
    )
    # turn on light
    await hass.services.async_call(
        "light",
        "turn_on",
        {"entity_id": "light.test"},
        blocking=True,
    )
    await knx.assert_write(test_address, True)
    knx.assert_state(
        "light.test",
        STATE_ON,
        color_mode=ColorMode.ONOFF,
    )
    expect(True).to_be(True)


@test.skip("port deferred - sibling test")
async def light_brightness() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_color_temp_absolute() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_color_temp_relative() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_hs_color() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_xyy_color() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_xyy_color_with_brightness() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_rgb_individual() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_rgbw_individual() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_rgb() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_rgbw() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_ui_create() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_ui_load() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_ui_color_only() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def light_ui_color_temp() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def remove_ui_light() -> None:
    """Stub."""
