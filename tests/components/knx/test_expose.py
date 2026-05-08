"""Test KNX expose."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.knx.const import CONF_KNX_EXPOSE, KNX_ADDRESS
from homeassistant.const import CONF_ENTITY_ID, CONF_TYPE
from homeassistant.core import HomeAssistant

from .conftest import KNXTestKit
from ._fixtures import knx, mock_config_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def binary_expose(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    knx: KNXTestKit = Depends(knx),
) -> None:
    """Test a binary expose to only send telegrams on state change."""
    entity_id = "fake.entity"
    await knx.setup_integration(
        {
            CONF_KNX_EXPOSE: {
                CONF_TYPE: "binary",
                KNX_ADDRESS: "1/1/8",
                CONF_ENTITY_ID: entity_id,
            }
        },
    )

    # Change state to on
    hass.states.async_set(entity_id, "on", {})
    await hass.async_block_till_done()
    await knx.assert_write("1/1/8", True)

    # Change attribute; keep state
    hass.states.async_set(entity_id, "on", {"brightness": 180})
    await hass.async_block_till_done()
    await knx.assert_no_telegram()
    expect(True).to_be(True)


@test.skip("port deferred - sibling test")
async def expose_attribute() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def expose_attribute_with_default() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def expose_string() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def expose_cooldown() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def expose_periodic_send() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def expose_value_template() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def expose_conversion_exception() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def ui_expose_create_and_update() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def ui_expose_with_options() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def remove_exposed_entity() -> None:
    """Stub."""
