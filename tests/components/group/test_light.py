"""The tests for the Group Light platform."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.group import DOMAIN
from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_EFFECT,
    ATTR_EFFECT_LIST,
    ATTR_HS_COLOR,
    DOMAIN as LIGHT_DOMAIN,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    STATE_ON,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from homeassistant.setup import async_setup_component

from tests.hass_fixtures import (
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
) -> None:
    """Anchor fixture for tryke fixture-injection."""


@test
async def default_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test light group default state."""
    hass.states.async_set("light.kitchen", "on")
    await async_setup_component(
        hass,
        LIGHT_DOMAIN,
        {
            LIGHT_DOMAIN: {
                "platform": DOMAIN,
                "entities": ["light.kitchen", "light.bedroom"],
                "name": "Bedroom Group",
                "unique_id": "unique_identifier",
                "all": "false",
            }
        },
    )
    await hass.async_block_till_done()
    await hass.async_start()
    await hass.async_block_till_done()

    state = hass.states.get("light.bedroom_group")
    expect(state).not_.to_be(None)
    expect(state.state).to_equal(STATE_ON)
    expect(state.attributes[ATTR_SUPPORTED_FEATURES]).to_equal(0)
    expect(state.attributes.get(ATTR_ENTITY_ID)).to_equal(
        ["light.kitchen", "light.bedroom"]
    )
    expect(state.attributes.get(ATTR_BRIGHTNESS)).to_be(None)
    expect(state.attributes.get(ATTR_HS_COLOR)).to_be(None)
    expect(state.attributes.get(ATTR_COLOR_TEMP_KELVIN)).to_be(None)
    expect(state.attributes.get(ATTR_EFFECT_LIST)).to_be(None)
    expect(state.attributes.get(ATTR_EFFECT)).to_be(None)

    registry_entry = entity_registry.async_get("light.bedroom_group")
    expect(registry_entry).not_.to_be(None)
    expect(registry_entry.unique_id).to_equal("unique_identifier")


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_reporting_any() -> None:
    """Stub for test_state_reporting_any."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def state_reporting_all() -> None:
    """Stub for test_state_reporting_all."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def brightness() -> None:
    """Stub for test_brightness."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def color_hs() -> None:
    """Stub for test_color_hs."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def color_rgb() -> None:
    """Stub for test_color_rgb."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def color_rgbw() -> None:
    """Stub for test_color_rgbw."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def color_rgbww() -> None:
    """Stub for test_color_rgbww."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def white() -> None:
    """Stub for test_white."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def color_temp() -> None:
    """Stub for test_color_temp."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def emulated_color_temp_group() -> None:
    """Stub for test_emulated_color_temp_group."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def min_max_mireds() -> None:
    """Stub for test_min_max_mireds."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def effect_list() -> None:
    """Stub for test_effect_list."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def effect() -> None:
    """Stub for test_effect."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def supported_color_modes() -> None:
    """Stub for test_supported_color_modes."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def color_mode() -> None:
    """Stub for test_color_mode."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def color_mode2() -> None:
    """Stub for test_color_mode2."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def supported_features() -> None:
    """Stub for test_supported_features."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_calls() -> None:
    """Stub for test_service_calls."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def service_call_effect() -> None:
    """Stub for test_service_call_effect."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def invalid_service_calls() -> None:
    """Stub for test_invalid_service_calls."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reload() -> None:
    """Stub for test_reload."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reload_with_platform_not_setup() -> None:
    """Stub for test_reload_with_platform_not_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def reload_with_base_integration_platform_not_setup() -> None:
    """Stub for test_reload_with_base_integration_platform_not_setup."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def nested_group() -> None:
    """Stub for test_nested_group."""


@test.skip("pending tryke port - pytest fixtures need migration to _fixtures.py")
async def assumed_state() -> None:
    """Stub for test_assumed_state."""

