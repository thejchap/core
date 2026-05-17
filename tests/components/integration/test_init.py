"""Test the Integration - Riemann sum integral integration."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import integration
from homeassistant.components.integration.const import DOMAIN
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_entity_registry_updated_event

from tests.common import MockConfigEntry
from tests.components.integration._fixtures import (
    integration_config_entry as integration_config_entry_fx,
    sensor_config_entry as sensor_config_entry_fx,
    sensor_device as sensor_device_fx,
    sensor_entity_entry as sensor_entity_entry_fx,
)
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fx,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts the test module into Tryke's HookExecutor path."""
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
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test setting up and removing a config entry."""
    input_sensor_entity_id = "sensor.input"
    integration_entity_id = "sensor.my_integration"

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "method": "trapezoidal",
            "name": "My integration",
            "round": 1.0,
            "source": "sensor.input",
            "unit_prefix": "k",
            "unit_time": "min",
            "max_sub_interval": {"minutes": 1},
        },
        title="My integration",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(entity_registry.async_get(integration_entity_id) is not None).to_be(True)

    state = hass.states.get(integration_entity_id)
    expect(state.state).to_equal("unknown")
    expect("unit_of_measurement" not in state.attributes).to_be(True)
    expect(state.attributes["source"]).to_equal("sensor.input")

    hass.states.async_set(input_sensor_entity_id, 10, {"unit_of_measurement": "cat"})
    hass.states.async_set(input_sensor_entity_id, 11, {"unit_of_measurement": "cat"})
    await hass.async_block_till_done()
    state = hass.states.get(integration_entity_id)
    expect(state.state).not_.to_equal("unknown")
    expect(state.attributes["unit_of_measurement"]).to_equal("kcatmin")

    # Remove the config entry
    expect(
        await hass.config_entries.async_remove(config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(hass.states.get(integration_entity_id)).to_be_none()
    expect(entity_registry.async_get(integration_entity_id)).to_be_none()


@test
async def entry_changed(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test reconfiguring."""
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    def _create_mock_entity(domain: str, name: str) -> er.RegistryEntry:
        config_entry = MockConfigEntry(
            data={},
            domain="test",
            title=f"{name}",
        )
        config_entry.add_to_hass(hass)
        device_entry = device_registry.async_get_or_create(
            identifiers={("test", name)}, config_entry_id=config_entry.entry_id
        )
        return entity_registry.async_get_or_create(
            domain, "test", name, suggested_object_id=name, device_id=device_entry.id
        )

    def _get_device_config_entries(entry: er.RegistryEntry) -> set[str]:
        expect(entry.device_id).to_be_truthy()
        device = device_registry.async_get(entry.device_id)
        expect(device).to_be_truthy()
        return device.config_entries

    # Set up entities, with backing devices and config entries
    input_entry = _create_mock_entity("sensor", "input")
    valid_entry = _create_mock_entity("sensor", "valid")
    expect(input_entry.device_id != valid_entry.device_id).to_be(True)

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "method": "left",
            "name": "My integration",
            "source": "sensor.input",
            "unit_time": "min",
        },
        title="My integration",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(
        config_entry.entry_id not in _get_device_config_entries(input_entry)
    ).to_be(True)
    expect(
        config_entry.entry_id not in _get_device_config_entries(valid_entry)
    ).to_be(True)
    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    expect(integration_entity_entry.device_id).to_equal(input_entry.device_id)

    hass.config_entries.async_update_entry(
        config_entry, options={**config_entry.options, "source": "sensor.valid"}
    )
    hass.config_entries.async_schedule_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Check that the device association has updated
    expect(
        config_entry.entry_id not in _get_device_config_entries(input_entry)
    ).to_be(True)
    expect(
        config_entry.entry_id not in _get_device_config_entries(valid_entry)
    ).to_be(True)
    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    expect(integration_entity_entry.device_id).to_equal(valid_entry.device_id)


@test
async def async_handle_source_entity_changes_source_entity_removed(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    integration_config_entry: MockConfigEntry = Depends(integration_config_entry_fx),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the integration config entry is removed when the source entity is removed."""
    expect(
        await hass.config_entries.async_setup(integration_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    expect(integration_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(integration_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, integration_entity_entry.entity_id)

    # Remove the source sensor's config entry from the device, this removes the
    # source sensor
    with patch(
        "homeassistant.components.integration.async_unload_entry",
        wraps=integration.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_not_called()

    # Check that the entity is no longer linked to the source device
    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    expect(integration_entity_entry.device_id).to_be_none()

    # Check that the device is removed
    expect(device_registry.async_get(sensor_device.id)).to_be_falsy()

    # Check that the integration config entry is not removed
    expect(
        integration_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_changes_source_entity_removed_shared_device(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    integration_config_entry: MockConfigEntry = Depends(integration_config_entry_fx),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the integration config entry is removed when the source entity is removed."""
    # Add another config entry to the sensor device
    other_config_entry = MockConfigEntry()
    other_config_entry.add_to_hass(hass)
    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=other_config_entry.entry_id
    )

    expect(
        await hass.config_entries.async_setup(integration_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    expect(integration_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(integration_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, integration_entity_entry.entity_id)

    with patch(
        "homeassistant.components.integration.async_unload_entry",
        wraps=integration.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_not_called()

    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    expect(integration_entity_entry.device_id).to_be_none()

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(integration_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    expect(
        integration_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_changes_source_entity_removed_from_device(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    integration_config_entry: MockConfigEntry = Depends(integration_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the source entity removed from the source device."""
    expect(
        await hass.config_entries.async_setup(integration_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    expect(integration_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(integration_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, integration_entity_entry.entity_id)

    with patch(
        "homeassistant.components.integration.async_unload_entry",
        wraps=integration.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=None
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    expect(integration_entity_entry.device_id).to_be_none()

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(integration_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    expect(
        integration_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_changes_source_entity_moved_other_device(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    integration_config_entry: MockConfigEntry = Depends(integration_config_entry_fx),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the source entity is moved to another device."""
    sensor_device_2 = device_registry.async_get_or_create(
        config_entry_id=sensor_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:FF")},
    )

    expect(
        await hass.config_entries.async_setup(integration_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    expect(integration_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(integration_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    expect(integration_config_entry.entry_id in sensor_device_2.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, integration_entity_entry.entity_id)

    with patch(
        "homeassistant.components.integration.async_unload_entry",
        wraps=integration.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=sensor_device_2.id
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    expect(integration_entity_entry.device_id).to_equal(sensor_device_2.id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(integration_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    expect(integration_config_entry.entry_id in sensor_device_2.config_entries).to_be(
        False
    )

    expect(
        integration_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_new_entity_id(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    integration_config_entry: MockConfigEntry = Depends(integration_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the source entity's entity ID is changed."""
    expect(
        await hass.config_entries.async_setup(integration_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    expect(integration_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(integration_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, integration_entity_entry.entity_id)

    with patch(
        "homeassistant.components.integration.async_unload_entry",
        wraps=integration.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, new_entity_id="sensor.new_entity_id"
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    expect(integration_config_entry.options["source"]).to_equal("sensor.new_entity_id")

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(integration_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    expect(
        integration_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal([])


@test
async def migration_1_1(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
) -> None:
    """Test migration from v1.1 removes integration config entry from device."""
    integration_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "method": "trapezoidal",
            "name": "My integration",
            "round": 1.0,
            "source": sensor_entity_entry.entity_id,
            "unit_prefix": "k",
            "unit_time": "min",
            "max_sub_interval": {"minutes": 1},
        },
        title="My integration",
        version=1,
        minor_version=1,
    )
    integration_config_entry.add_to_hass(hass)

    # Add the helper config entry to the device
    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=integration_config_entry.entry_id
    )

    # Check preconditions
    sensor_device = device_registry.async_get(sensor_device.id)
    expect(integration_config_entry.entry_id in sensor_device.config_entries).to_be(
        True
    )

    await hass.config_entries.async_setup(integration_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(integration_config_entry.state).to_be(ConfigEntryState.LOADED)

    # Check that the helper config entry is removed from the device and the helper
    # entity is linked to the source device
    sensor_device = device_registry.async_get(sensor_device.id)
    expect(integration_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )
    integration_entity_entry = entity_registry.async_get("sensor.my_integration")
    expect(integration_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    expect(integration_config_entry.version).to_equal(1)
    expect(integration_config_entry.minor_version).to_equal(2)


@test
async def migration_from_future_version(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test migration from future version."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "method": "trapezoidal",
            "name": "My integration",
            "round": 1.0,
            "source": "sensor.test",
            "unit_prefix": "k",
            "unit_time": "min",
            "max_sub_interval": {"minutes": 1},
        },
        title="My integration",
        version=2,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
