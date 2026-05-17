"""Test the Trend integration."""

from __future__ import annotations

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import trend
from homeassistant.components.trend.const import DOMAIN
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_entity_registry_updated_event

from ._fixtures import (
    ComponentSetup,
    config_entry as config_entry_fixture,
    sensor_config_entry as sensor_config_entry_fixture,
    sensor_device as sensor_device_fixture,
    sensor_entity_entry as sensor_entity_entry_fixture,
    setup_component as setup_component_fixture,
    trend_config_entry as trend_config_entry_fixture,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Present so tryke builds a fixture executor for this module."""
    return 0


def track_entity_registry_actions(hass: HomeAssistant, entity_id: str) -> list[str]:
    """Track entity registry actions for an entity."""
    events = []

    @callback
    def add_event(event: Event[er.EventEntityRegistryUpdatedData]) -> None:
        """Add entity registry updated event to the list."""
        events.append(event.data["action"])

    async_track_entity_registry_updated_event(hass, entity_id, add_event)

    return events


@test
async def setup_and_remove_config_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test setting up and removing a config entry."""
    trend_entity_id = "binary_sensor.my_trend"

    # Set up the config entry
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    # Check the entity is registered in the entity registry
    expect(entity_registry.async_get(trend_entity_id)).not_.to_be_none()

    # Remove the config entry
    expect(
        await hass.config_entries.async_remove(config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    # Check the state and entity registry entry are removed
    expect(hass.states.get(trend_entity_id)).to_be_none()
    expect(entity_registry.async_get(trend_entity_id)).to_be_none()


@test
async def reload_config_entry(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
    setup_component: ComponentSetup = Depends(setup_component_fixture),
) -> None:
    """Test config entry reload."""
    await setup_component({})

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(
        hass.config_entries.async_update_entry(
            config_entry, data={**config_entry.data, "max_samples": 4.0}
        )
    ).to_be_truthy()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.data).to_equal({**config_entry.data, "max_samples": 4.0})


@test
async def async_handle_source_entity_changes_source_entity_removed(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    trend_config_entry: MockConfigEntry = Depends(trend_config_entry_fixture),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry_fixture),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fixture),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fixture),
) -> None:
    """Test the trend config entry is removed when the source entity is removed."""
    expect(
        await hass.config_entries.async_setup(trend_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    trend_entity_entry = entity_registry.async_get("binary_sensor.my_trend")
    expect(trend_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(sensor_device.config_entries).not_.to_contain(trend_config_entry.entry_id)

    events = track_entity_registry_actions(hass, trend_entity_entry.entity_id)

    # Remove the source sensor's config entry from the device, this removes the
    # source sensor
    with patch(
        "homeassistant.components.trend.async_unload_entry",
        wraps=trend.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the helper entity is removed
    expect(entity_registry.async_get("binary_sensor.my_trend")).to_be_none()

    # Check that the device is removed
    expect(device_registry.async_get(sensor_device.id)).to_be_none()

    # Check that the trend config entry is removed
    expect(hass.config_entries.async_entry_ids()).not_.to_contain(
        trend_config_entry.entry_id
    )

    # Check we got the expected events
    expect(events).to_equal(["remove"])


@test
async def async_handle_source_entity_changes_source_entity_removed_shared_device(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    trend_config_entry: MockConfigEntry = Depends(trend_config_entry_fixture),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry_fixture),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fixture),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fixture),
) -> None:
    """Test the trend config entry is removed when the source entity is removed."""
    # Add another config entry to the sensor device
    other_config_entry = MockConfigEntry()
    other_config_entry.add_to_hass(hass)
    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=other_config_entry.entry_id
    )

    expect(
        await hass.config_entries.async_setup(trend_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    trend_entity_entry = entity_registry.async_get("binary_sensor.my_trend")
    expect(trend_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(sensor_device.config_entries).not_.to_contain(trend_config_entry.entry_id)

    events = track_entity_registry_actions(hass, trend_entity_entry.entity_id)

    # Remove the source sensor's config entry from the device, this removes the
    # source sensor
    with patch(
        "homeassistant.components.trend.async_unload_entry",
        wraps=trend.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the helper entity is removed
    expect(entity_registry.async_get("binary_sensor.my_trend")).to_be_none()

    # Check that the trend config entry is not in the device
    sensor_device = device_registry.async_get(sensor_device.id)
    expect(sensor_device.config_entries).not_.to_contain(trend_config_entry.entry_id)

    # Check that the trend config entry is removed
    expect(hass.config_entries.async_entry_ids()).not_.to_contain(
        trend_config_entry.entry_id
    )

    # Check we got the expected events
    expect(events).to_equal(["remove"])


@test
async def async_handle_source_entity_changes_source_entity_removed_from_device(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    trend_config_entry: MockConfigEntry = Depends(trend_config_entry_fixture),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fixture),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fixture),
) -> None:
    """Test the source entity removed from the source device."""
    expect(
        await hass.config_entries.async_setup(trend_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    trend_entity_entry = entity_registry.async_get("binary_sensor.my_trend")
    expect(trend_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(sensor_device.config_entries).not_.to_contain(trend_config_entry.entry_id)

    events = track_entity_registry_actions(hass, trend_entity_entry.entity_id)

    # Remove the source sensor from the device
    with patch(
        "homeassistant.components.trend.async_unload_entry",
        wraps=trend.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=None
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the entity is no longer linked to the source device
    trend_entity_entry = entity_registry.async_get("binary_sensor.my_trend")
    expect(trend_entity_entry.device_id).to_be_none()

    # Check that the trend config entry is not in the device
    sensor_device = device_registry.async_get(sensor_device.id)
    expect(sensor_device.config_entries).not_.to_contain(trend_config_entry.entry_id)

    # Check that the trend config entry is not removed
    expect(hass.config_entries.async_entry_ids()).to_contain(
        trend_config_entry.entry_id
    )

    # Check we got the expected events
    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_changes_source_entity_moved_other_device(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    trend_config_entry: MockConfigEntry = Depends(trend_config_entry_fixture),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry_fixture),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fixture),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fixture),
) -> None:
    """Test the source entity is moved to another device."""
    sensor_device_2 = device_registry.async_get_or_create(
        config_entry_id=sensor_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:FF")},
    )

    expect(
        await hass.config_entries.async_setup(trend_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    trend_entity_entry = entity_registry.async_get("binary_sensor.my_trend")
    expect(trend_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(sensor_device.config_entries).not_.to_contain(trend_config_entry.entry_id)
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    expect(sensor_device_2.config_entries).not_.to_contain(trend_config_entry.entry_id)

    events = track_entity_registry_actions(hass, trend_entity_entry.entity_id)

    # Move the source sensor to another device
    with patch(
        "homeassistant.components.trend.async_unload_entry",
        wraps=trend.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=sensor_device_2.id
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the entity is linked to the other device
    trend_entity_entry = entity_registry.async_get("binary_sensor.my_trend")
    expect(trend_entity_entry.device_id).to_equal(sensor_device_2.id)

    # Check that the trend config entry is not in any of the devices
    sensor_device = device_registry.async_get(sensor_device.id)
    expect(sensor_device.config_entries).not_.to_contain(trend_config_entry.entry_id)
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    expect(sensor_device_2.config_entries).not_.to_contain(trend_config_entry.entry_id)

    # Check that the trend config entry is not removed
    expect(hass.config_entries.async_entry_ids()).to_contain(
        trend_config_entry.entry_id
    )

    # Check we got the expected events
    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_new_entity_id(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    trend_config_entry: MockConfigEntry = Depends(trend_config_entry_fixture),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fixture),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fixture),
) -> None:
    """Test the source entity's entity ID is changed."""
    expect(
        await hass.config_entries.async_setup(trend_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    trend_entity_entry = entity_registry.async_get("binary_sensor.my_trend")
    expect(trend_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(sensor_device.config_entries).not_.to_contain(trend_config_entry.entry_id)

    events = track_entity_registry_actions(hass, trend_entity_entry.entity_id)

    # Change the source entity's entity ID
    with patch(
        "homeassistant.components.trend.async_unload_entry",
        wraps=trend.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, new_entity_id="sensor.new_entity_id"
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    # Check that the trend config entry is updated with the new entity ID
    expect(trend_config_entry.options["entity_id"]).to_equal("sensor.new_entity_id")

    # Check that the helper config is not in the device
    sensor_device = device_registry.async_get(sensor_device.id)
    expect(sensor_device.config_entries).not_.to_contain(trend_config_entry.entry_id)

    # Check that the trend config entry is not removed
    expect(hass.config_entries.async_entry_ids()).to_contain(
        trend_config_entry.entry_id
    )

    # Check we got the expected events
    expect(events).to_equal([])


@test
async def migration_1_1(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fixture),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fixture),
) -> None:
    """Test migration from v1.1 removes trend config entry from device."""

    trend_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My trend",
            "entity_id": sensor_entity_entry.entity_id,
            "invert": False,
        },
        title="My trend",
        version=1,
        minor_version=1,
    )
    trend_config_entry.add_to_hass(hass)

    # Add the helper config entry to the device
    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=trend_config_entry.entry_id
    )

    # Check preconditions
    sensor_device = device_registry.async_get(sensor_device.id)
    expect(sensor_device.config_entries).to_contain(trend_config_entry.entry_id)

    await hass.config_entries.async_setup(trend_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(trend_config_entry.state).to_be(ConfigEntryState.LOADED)

    # Check that the helper config entry is removed from the device and the helper
    # entity is linked to the source device
    sensor_device = device_registry.async_get(sensor_device.id)
    expect(sensor_device.config_entries).not_.to_contain(trend_config_entry.entry_id)
    trend_entity_entry = entity_registry.async_get("binary_sensor.my_trend")
    expect(trend_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    expect(trend_config_entry.version).to_equal(1)
    expect(trend_config_entry.minor_version).to_equal(2)


@test
async def migration_from_future_version(
    _trigger: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migration from future version."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My trend",
            "entity_id": "sensor.test",
            "invert": False,
        },
        title="My trend",
        version=2,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
