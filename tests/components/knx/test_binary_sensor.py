"""Test KNX binary sensor."""

from tryke import Depends, expect, fixture, test

from homeassistant.components.knx.schema import BinarySensorSchema
from homeassistant.const import (
    CONF_ENTITY_CATEGORY,
    CONF_NAME,
    EntityCategory,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from .conftest import KNXTestKit
from ._fixtures import knx, mock_config_entry

from tests.hass_fixtures import (
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Module-level fixture anchor."""


@test
async def binary_sensor_entity_category(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    knx: KNXTestKit = Depends(knx),
) -> None:
    """Test KNX binary sensor entity category."""
    await knx.setup_integration(
        {
            BinarySensorSchema.PLATFORM: [
                {
                    CONF_NAME: "test_normal",
                    "state_address": "1/1/1",
                    CONF_ENTITY_CATEGORY: EntityCategory.DIAGNOSTIC,
                },
            ]
        }
    )

    await knx.assert_read("1/1/1")
    await knx.receive_response("1/1/1", True)

    entity = entity_registry.async_get("binary_sensor.test_normal")
    expect(entity.entity_category is EntityCategory.DIAGNOSTIC).to_be(True)


@test.skip("port deferred - sibling test")
async def binary_sensor() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def last_reported() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def binary_sensor_ignore_internal_state() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def binary_sensor_counter() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def binary_sensor_reset() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def binary_sensor_restore() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def binary_sensor_restore_invert() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def binary_sensor_ui_create() -> None:
    """Stub."""


@test.skip("port deferred - sibling test")
async def binary_sensor_ui_load() -> None:
    """Stub."""
