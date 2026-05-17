"""Test the Min/Max integration."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import threshold
from homeassistant.components.threshold.const import DOMAIN
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_entity_registry_updated_event

from tests.common import MockConfigEntry
from tests.components.threshold._fixtures import (
    sensor_config_entry as sensor_config_entry_fx,
    sensor_device as sensor_device_fx,
    sensor_entity_entry as sensor_entity_entry_fx,
    threshold_config_entry as threshold_config_entry_fx,
)
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fx,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Module-local anchor; opts into Tryke's HookExecutor path."""
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


@test.cases(test.case("binary_sensor", platform="binary_sensor"))
async def setup_and_remove_config_entry(
    platform: str,
    hass: HomeAssistant = Depends(hass_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
) -> None:
    """Test setting up and removing a config entry."""
    hass.states.async_set("sensor.input", "-10")

    input_sensor = "sensor.input"

    threshold_entity_id = f"{platform}.input_threshold"

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entity_id": input_sensor,
            "hysteresis": 0.0,
            "lower": -2.0,
            "name": "Input threshold",
            "upper": None,
        },
        title="Input threshold",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(entity_registry.async_get(threshold_entity_id) is not None).to_be(True)

    state = hass.states.get(threshold_entity_id)
    expect(state is not None).to_be(True)
    expect(state.state).to_equal("on")
    expect(state.attributes["entity_id"]).to_equal(input_sensor)
    expect(state.attributes["hysteresis"]).to_equal(0.0)
    expect(state.attributes["lower"]).to_equal(-2.0)
    expect(state.attributes["position"]).to_equal("below")
    expect(state.attributes["sensor_value"]).to_equal(-10.0)
    expect(state.attributes["type"]).to_equal("lower")
    expect(state.attributes["upper"]).to_be(None)

    expect(await hass.config_entries.async_remove(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(hass.states.get(threshold_entity_id)).to_be(None)
    expect(entity_registry.async_get(threshold_entity_id)).to_be(None)


@test.cases(test.case("sensor", platform="sensor"))
async def entry_changed(
    platform: str,
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

    run1_entry = _create_mock_entity("sensor", "initial")
    run2_entry = _create_mock_entity("sensor", "changed")
    expect(run1_entry.device_id != run2_entry.device_id).to_be(True)

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entity_id": "sensor.initial",
            "hysteresis": 0.0,
            "lower": -2.0,
            "name": "My threshold",
            "upper": None,
        },
        title="My threshold",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(config_entry.entry_id not in _get_device_config_entries(run1_entry)).to_be(
        True
    )
    expect(config_entry.entry_id not in _get_device_config_entries(run2_entry)).to_be(
        True
    )
    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    expect(threshold_entity_entry.device_id).to_equal(run1_entry.device_id)

    hass.config_entries.async_update_entry(
        config_entry, options={**config_entry.options, "entity_id": "sensor.changed"}
    )
    hass.config_entries.async_schedule_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.entry_id not in _get_device_config_entries(run1_entry)).to_be(
        True
    )
    expect(config_entry.entry_id not in _get_device_config_entries(run2_entry)).to_be(
        True
    )
    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    expect(threshold_entity_entry.device_id).to_equal(run2_entry.device_id)


@test
async def async_handle_source_entity_changes_source_entity_removed(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    threshold_config_entry: MockConfigEntry = Depends(threshold_config_entry_fx),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the threshold config entry is removed when the source entity is removed."""
    expect(
        await hass.config_entries.async_setup(threshold_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    expect(threshold_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(threshold_config_entry.entry_id not in sensor_device.config_entries).to_be(
        True
    )

    events = track_entity_registry_actions(hass, threshold_entity_entry.entity_id)

    with patch(
        "homeassistant.components.threshold.async_unload_entry",
        wraps=threshold.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_not_called()

    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    expect(threshold_entity_entry.device_id).to_be(None)

    expect(device_registry.async_get(sensor_device.id)).to_be_falsy()

    expect(
        threshold_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_changes_source_entity_removed_shared_device(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    threshold_config_entry: MockConfigEntry = Depends(threshold_config_entry_fx),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the threshold config entry is removed when the source entity is removed."""
    other_config_entry = MockConfigEntry()
    other_config_entry.add_to_hass(hass)
    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=other_config_entry.entry_id
    )

    expect(
        await hass.config_entries.async_setup(threshold_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    expect(threshold_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(threshold_config_entry.entry_id not in sensor_device.config_entries).to_be(
        True
    )

    events = track_entity_registry_actions(hass, threshold_entity_entry.entity_id)

    with patch(
        "homeassistant.components.threshold.async_unload_entry",
        wraps=threshold.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_not_called()

    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    expect(threshold_entity_entry.device_id).to_be(None)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(threshold_config_entry.entry_id not in sensor_device.config_entries).to_be(
        True
    )

    expect(
        threshold_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_changes_source_entity_removed_from_device(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    threshold_config_entry: MockConfigEntry = Depends(threshold_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the source entity removed from the source device."""
    expect(
        await hass.config_entries.async_setup(threshold_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    expect(threshold_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(threshold_config_entry.entry_id not in sensor_device.config_entries).to_be(
        True
    )

    events = track_entity_registry_actions(hass, threshold_entity_entry.entity_id)

    with patch(
        "homeassistant.components.threshold.async_unload_entry",
        wraps=threshold.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=None
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    expect(threshold_entity_entry.device_id).to_be(None)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(threshold_config_entry.entry_id not in sensor_device.config_entries).to_be(
        True
    )

    expect(
        threshold_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_changes_source_entity_moved_other_device(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    threshold_config_entry: MockConfigEntry = Depends(threshold_config_entry_fx),
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
        await hass.config_entries.async_setup(threshold_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    expect(threshold_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(threshold_config_entry.entry_id not in sensor_device.config_entries).to_be(
        True
    )
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    expect(threshold_config_entry.entry_id not in sensor_device_2.config_entries).to_be(
        True
    )

    events = track_entity_registry_actions(hass, threshold_entity_entry.entity_id)

    with patch(
        "homeassistant.components.threshold.async_unload_entry",
        wraps=threshold.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=sensor_device_2.id
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    expect(threshold_entity_entry.device_id).to_equal(sensor_device_2.id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(threshold_config_entry.entry_id not in sensor_device.config_entries).to_be(
        True
    )
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    expect(threshold_config_entry.entry_id not in sensor_device_2.config_entries).to_be(
        True
    )

    expect(
        threshold_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_new_entity_id(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    threshold_config_entry: MockConfigEntry = Depends(threshold_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the source entity's entity ID is changed."""
    expect(
        await hass.config_entries.async_setup(threshold_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    expect(threshold_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(threshold_config_entry.entry_id not in sensor_device.config_entries).to_be(
        True
    )

    events = track_entity_registry_actions(hass, threshold_entity_entry.entity_id)

    with patch(
        "homeassistant.components.threshold.async_unload_entry",
        wraps=threshold.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, new_entity_id="sensor.new_entity_id"
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    expect(threshold_config_entry.options["entity_id"]).to_equal("sensor.new_entity_id")

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(threshold_config_entry.entry_id not in sensor_device.config_entries).to_be(
        True
    )

    expect(
        threshold_config_entry.entry_id in hass.config_entries.async_entry_ids()
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
    """Test migration from v1.1 removes threshold config entry from device."""

    threshold_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entity_id": sensor_entity_entry.entity_id,
            "hysteresis": 0.0,
            "lower": -2.0,
            "name": "My threshold",
            "upper": None,
        },
        title="My threshold",
        version=1,
        minor_version=1,
    )
    threshold_config_entry.add_to_hass(hass)

    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=threshold_config_entry.entry_id
    )

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(threshold_config_entry.entry_id in sensor_device.config_entries).to_be(True)

    await hass.config_entries.async_setup(threshold_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(threshold_config_entry.state).to_be(ConfigEntryState.LOADED)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(threshold_config_entry.entry_id not in sensor_device.config_entries).to_be(
        True
    )
    threshold_entity_entry = entity_registry.async_get("binary_sensor.my_threshold")
    expect(threshold_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    expect(threshold_config_entry.version).to_equal(1)
    expect(threshold_config_entry.minor_version).to_equal(2)


@test
async def migration_from_future_version(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test migration from future version."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entity_id": "sensor.test",
            "hysteresis": 0.0,
            "lower": -2.0,
            "name": "My threshold",
            "upper": None,
        },
        title="My threshold",
        version=2,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
