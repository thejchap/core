"""Test template helper functions."""

from tryke import Depends, expect, fixture, test

from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    area_registry as ar,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.template.helpers import raise_no_default, resolve_area_id

from tests.common import MockConfigEntry
from tests.hass_fixtures import area_registry, device_registry, entity_registry, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
def raise_no_default_helper() -> None:
    """Test raise_no_default raises ValueError with correct message."""
    expect(lambda: raise_no_default("test", "invalid")).to_raise(
        ValueError,
        match=(
            "Template error: test got invalid input 'invalid' when rendering or"
            " compiling template '' but no default was specified"
        ),
    )


@test
async def resolve_area_id_test(
    hass: HomeAssistant = Depends(hass),
    area_registry: ar.AreaRegistry = Depends(area_registry),
    device_registry: dr.DeviceRegistry = Depends(device_registry),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test resolve_area_id function."""
    config_entry = MockConfigEntry(domain="light")
    config_entry.add_to_hass(hass)

    # Test non existing entity id
    expect(resolve_area_id(hass, "sensor.fake")).to_be(None)

    # Test non existing device id (hex value)
    expect(resolve_area_id(hass, "123abc")).to_be(None)

    # Test non existing area name
    expect(resolve_area_id(hass, "fake area name")).to_be(None)

    # Test wrong value type
    expect(resolve_area_id(hass, 56)).to_be(None)

    area_registry.async_get_or_create("sensor.fake")

    # Test device with single entity, which has no area
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        "light",
        "hue",
        "5678",
        config_entry=config_entry,
        device_id=device_entry.id,
    )
    expect(resolve_area_id(hass, device_entry.id)).to_be(None)
    expect(resolve_area_id(hass, entity_entry.entity_id)).to_be(None)

    # Test device ID, entity ID and area name as input with area name that looks like
    # a device ID
    area_entry_hex = area_registry.async_get_or_create("123abc")
    device_entry = device_registry.async_update_device(
        device_entry.id, area_id=area_entry_hex.id
    )
    entity_entry = entity_registry.async_update_entity(
        entity_entry.entity_id, area_id=area_entry_hex.id
    )

    expect(resolve_area_id(hass, device_entry.id)).to_equal(area_entry_hex.id)
    expect(resolve_area_id(hass, entity_entry.entity_id)).to_equal(area_entry_hex.id)
    expect(resolve_area_id(hass, area_entry_hex.name)).to_equal(area_entry_hex.id)

    # Test device ID, entity ID and area name as input with area name that looks like
    # an entity ID
    area_entry_entity_id = area_registry.async_get_or_create("sensor.fake")
    device_entry = device_registry.async_update_device(
        device_entry.id, area_id=area_entry_entity_id.id
    )
    entity_entry = entity_registry.async_update_entity(
        entity_entry.entity_id, area_id=area_entry_entity_id.id
    )

    expect(resolve_area_id(hass, device_entry.id)).to_equal(area_entry_entity_id.id)
    expect(resolve_area_id(hass, entity_entry.entity_id)).to_equal(
        area_entry_entity_id.id
    )
    expect(resolve_area_id(hass, area_entry_entity_id.name)).to_equal(
        area_entry_entity_id.id
    )

    # Make sure that when entity doesn't have an area but its device does, that's what
    # gets returned
    entity_entry = entity_registry.async_update_entity(
        entity_entry.entity_id, area_id=None
    )

    expect(resolve_area_id(hass, entity_entry.entity_id)).to_equal(
        area_entry_entity_id.id
    )

    # Test area alias
    area_with_alias = area_registry.async_get_or_create("Living Room")
    area_registry.async_update(area_with_alias.id, aliases={"lounge", "family room"})

    expect(resolve_area_id(hass, "Living Room")).to_equal(area_with_alias.id)
    expect(resolve_area_id(hass, "lounge")).to_equal(area_with_alias.id)
    expect(resolve_area_id(hass, "family room")).to_equal(area_with_alias.id)
