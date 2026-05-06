"""Tests for the Device Utils."""

from tryke import Depends, expect, fixture, test
import voluptuous as vol

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.device import (
    async_device_info_to_link_from_device_id,
    async_device_info_to_link_from_entity,
    async_entity_id_to_device,
    async_entity_id_to_device_id,
    async_remove_stale_devices_links_keep_current_device,
    async_remove_stale_devices_links_keep_entity_device,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import device_registry, entity_registry, hass


@fixture
def _trigger_executor() -> int:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return 0


@test
async def entity_id_to_device_device_id(
    hass: HomeAssistant = Depends(hass),
    device_registry: dr.DeviceRegistry = Depends(device_registry),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test returning an entity's device / device ID."""
    config_entry = MockConfigEntry(domain="my")
    config_entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        identifiers={("test", "current_device")},
        connections={("mac", "30:31:32:33:34:00")},
        config_entry_id=config_entry.entry_id,
    )
    expect(device).not_.to_be_none()

    # Entity registry
    entity = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source",
        config_entry=config_entry,
        device_id=device.id,
    )
    await hass.async_block_till_done()
    expect(entity_registry.async_get("sensor.test_source")).not_.to_be_none()

    device_id = async_entity_id_to_device_id(
        hass,
        entity_id_or_uuid=entity.entity_id,
    )
    expect(device_id).to_equal(device.id)
    expect(
        async_entity_id_to_device(
            hass,
            entity_id_or_uuid=entity.entity_id,
        )
    ).to_equal(device)

    expect(
        async_entity_id_to_device_id(
            hass,
            entity_id_or_uuid="unknown.entity_id",
        )
    ).to_be_none()
    expect(
        async_entity_id_to_device(
            hass,
            entity_id_or_uuid="unknown.entity_id",
        )
    ).to_be_none()

    device_id = async_entity_id_to_device_id(
        hass,
        entity_id_or_uuid=entity.id,
    )
    expect(device_id).to_equal(device.id)
    expect(
        async_entity_id_to_device(
            hass,
            entity_id_or_uuid=entity.id,
        )
    ).to_equal(device)

    expect(
        lambda: async_entity_id_to_device_id(
            hass,
            entity_id_or_uuid="unknown_uuid",
        )
    ).to_raise(vol.Invalid)

    expect(
        lambda: async_entity_id_to_device(
            hass,
            entity_id_or_uuid="unknown_uuid",
        )
    ).to_raise(vol.Invalid)


@test
async def device_info_to_link(
    hass: HomeAssistant = Depends(hass),
    device_registry: dr.DeviceRegistry = Depends(device_registry),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test for returning device info with device link information."""
    config_entry = MockConfigEntry(domain="my")
    config_entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        identifiers={("test", "my_device")},
        connections={("mac", "30:31:32:33:34:00")},
        config_entry_id=config_entry.entry_id,
    )
    expect(device).not_.to_be_none()

    # Source entity registry
    source_entity = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "source",
        config_entry=config_entry,
        device_id=device.id,
    )
    await hass.async_block_till_done()
    expect(entity_registry.async_get("sensor.test_source")).not_.to_be_none()

    result = async_device_info_to_link_from_entity(
        hass, entity_id_or_uuid=source_entity.entity_id
    )
    expect(result).to_equal(
        {
            "identifiers": {("test", "my_device")},
            "connections": {("mac", "30:31:32:33:34:00")},
        }
    )

    result = async_device_info_to_link_from_device_id(hass, device_id=device.id)
    expect(result).to_equal(
        {
            "identifiers": {("test", "my_device")},
            "connections": {("mac", "30:31:32:33:34:00")},
        }
    )

    # With a non-existent entity id
    result = async_device_info_to_link_from_entity(
        hass, entity_id_or_uuid="sensor.invalid"
    )
    expect(result).to_be_none()

    # With a non-existent device id
    result = async_device_info_to_link_from_device_id(hass, device_id="abcdefghi")
    expect(result).to_be_none()

    # With a None device id
    result = async_device_info_to_link_from_device_id(hass, device_id=None)
    expect(result).to_be_none()


@test
async def remove_stale_device_links_keep_entity_device(
    hass: HomeAssistant = Depends(hass),
    device_registry: dr.DeviceRegistry = Depends(device_registry),
    entity_registry: er.EntityRegistry = Depends(entity_registry),
) -> None:
    """Test cleaning works for entity."""
    helper_config_entry = MockConfigEntry(domain="helper_integration")
    helper_config_entry.add_to_hass(hass)
    host_config_entry = MockConfigEntry(domain="host_integration")
    host_config_entry.add_to_hass(hass)

    current_device = device_registry.async_get_or_create(
        identifiers={("test", "current_device")},
        connections={("mac", "30:31:32:33:34:00")},
        config_entry_id=helper_config_entry.entry_id,
    )

    stale_device_1 = device_registry.async_get_or_create(
        identifiers={("test", "stale_device_1")},
        connections={("mac", "30:31:32:33:34:01")},
        config_entry_id=helper_config_entry.entry_id,
    )

    device_registry.async_get_or_create(
        identifiers={("test", "stale_device_2")},
        connections={("mac", "30:31:32:33:34:02")},
        config_entry_id=helper_config_entry.entry_id,
    )

    # Source entity
    source_entity = entity_registry.async_get_or_create(
        "sensor",
        "host_integration",
        "source",
        config_entry=host_config_entry,
        device_id=current_device.id,
    )
    expect(entity_registry.async_get(source_entity.entity_id)).not_.to_be_none()

    # Helper entity connected to a stale device
    helper_entity = entity_registry.async_get_or_create(
        "sensor",
        "helper_integration",
        "helper",
        config_entry=helper_config_entry,
        device_id=stale_device_1.id,
    )
    expect(entity_registry.async_get(helper_entity.entity_id)).not_.to_be_none()

    devices_helper_entry = device_registry.devices.get_devices_for_config_entry_id(
        helper_config_entry.entry_id
    )

    # 3 devices linked to the config entry are expected (1 current device + 2 stales)
    expect(len(devices_helper_entry)).to_equal(3)

    # Manual cleanup should unlink stale devices from the config entry
    async_remove_stale_devices_links_keep_entity_device(
        hass,
        entry_id=helper_config_entry.entry_id,
        source_entity_id_or_uuid=source_entity.entity_id,
    )

    await hass.async_block_till_done()

    devices_helper_entry = device_registry.devices.get_devices_for_config_entry_id(
        helper_config_entry.entry_id
    )

    expect(len(devices_helper_entry)).to_equal(1)
    expect(current_device in devices_helper_entry).to_be(True)
    expect(entity_registry.async_get(source_entity.entity_id)).not_.to_be_none()
    expect(entity_registry.async_get(helper_entity.entity_id)).not_.to_be_none()


@test
async def remove_stale_devices_links_keep_current_device(
    hass: HomeAssistant = Depends(hass),
    device_registry: dr.DeviceRegistry = Depends(device_registry),
) -> None:
    """Test cleanup works for device id."""
    config_entry = MockConfigEntry(domain="hue")
    config_entry.add_to_hass(hass)

    current_device = device_registry.async_get_or_create(
        identifiers={("test", "current_device")},
        connections={("mac", "30:31:32:33:34:00")},
        config_entry_id=config_entry.entry_id,
    )
    expect(current_device).not_.to_be_none()

    device_registry.async_get_or_create(
        identifiers={("test", "stale_device_1")},
        connections={("mac", "30:31:32:33:34:01")},
        config_entry_id=config_entry.entry_id,
    )

    device_registry.async_get_or_create(
        identifiers={("test", "stale_device_2")},
        connections={("mac", "30:31:32:33:34:02")},
        config_entry_id=config_entry.entry_id,
    )

    devices_config_entry = device_registry.devices.get_devices_for_config_entry_id(
        config_entry.entry_id
    )

    expect(len(devices_config_entry)).to_equal(3)

    async_remove_stale_devices_links_keep_current_device(
        hass,
        entry_id=config_entry.entry_id,
        current_device_id=current_device.id,
    )

    devices_config_entry = device_registry.devices.get_devices_for_config_entry_id(
        config_entry.entry_id
    )

    expect(len(devices_config_entry)).to_equal(1)
    expect(current_device in devices_config_entry).to_be(True)
