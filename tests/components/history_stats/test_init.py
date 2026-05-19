"""Test History stats component setup process."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import history_stats
from homeassistant.components.history_stats.config_flow import (
    HistoryStatsConfigFlowHandler,
)
from homeassistant.components.history_stats.const import (
    CONF_END,
    CONF_START,
    DEFAULT_NAME,
    DOMAIN,
)
from homeassistant.components.sensor import CONF_STATE_CLASS, SensorStateClass
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.const import CONF_ENTITY_ID, CONF_NAME, CONF_STATE, CONF_TYPE
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_entity_registry_updated_event

from ._fixtures import (
    history_stats_config_entry as history_stats_config_entry_fx,
    loaded_entry as loaded_entry_fx,
    recorder_mock,
    sensor_config_entry as sensor_config_entry_fx,
    sensor_device as sensor_device_fx,
    sensor_entity_entry as sensor_entity_entry_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: object = Depends(recorder_mock),
) -> None:
    """Force tryke fixture resolution before each test."""


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
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    loaded_entry: MockConfigEntry = Depends(loaded_entry_fx),
) -> None:
    """Test unload an entry."""
    expect(loaded_entry.state).to_be(ConfigEntryState.LOADED)
    expect(
        await hass.config_entries.async_unload(loaded_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(loaded_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def async_handle_source_entity_changes_source_entity_removed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    history_stats_config_entry: MockConfigEntry = Depends(
        history_stats_config_entry_fx
    ),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the history_stats config entry is removed when the source entity is removed."""
    expect(
        await hass.config_entries.async_setup(history_stats_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    history_stats_entity_entry = entity_registry.async_get("sensor.my_history_stats")
    expect(history_stats_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(history_stats_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, history_stats_entity_entry.entity_id)

    # Remove the source sensor's config entry from the device, this removes the
    # source sensor
    with patch(
        "homeassistant.components.history_stats.async_unload_entry",
        wraps=history_stats.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    expect(entity_registry.async_get("sensor.my_history_stats")).to_be_falsy()
    expect(device_registry.async_get(sensor_device.id)).to_be_falsy()
    expect(
        history_stats_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(False)
    expect(events).to_equal(["remove"])


@test
async def async_handle_source_entity_changes_source_entity_removed_shared_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    history_stats_config_entry: MockConfigEntry = Depends(
        history_stats_config_entry_fx
    ),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the history_stats config entry is removed when the source entity is removed."""
    other_config_entry = MockConfigEntry()
    other_config_entry.add_to_hass(hass)
    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=other_config_entry.entry_id
    )

    expect(
        await hass.config_entries.async_setup(history_stats_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    history_stats_entity_entry = entity_registry.async_get("sensor.my_history_stats")
    expect(history_stats_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(history_stats_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, history_stats_entity_entry.entity_id)

    with patch(
        "homeassistant.components.history_stats.async_unload_entry",
        wraps=history_stats.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    expect(entity_registry.async_get("sensor.my_history_stats")).to_be_falsy()
    sensor_device = device_registry.async_get(sensor_device.id)
    expect(history_stats_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )
    expect(
        history_stats_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(False)
    expect(events).to_equal(["remove"])


@test
async def async_handle_source_entity_changes_source_entity_removed_from_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    history_stats_config_entry: MockConfigEntry = Depends(
        history_stats_config_entry_fx
    ),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the source entity removed from the source device."""
    expect(
        await hass.config_entries.async_setup(history_stats_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    history_stats_entity_entry = entity_registry.async_get("sensor.my_history_stats")
    expect(history_stats_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(history_stats_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, history_stats_entity_entry.entity_id)

    with patch(
        "homeassistant.components.history_stats.async_unload_entry",
        wraps=history_stats.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=None
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    history_stats_entity_entry = entity_registry.async_get("sensor.my_history_stats")
    expect(history_stats_entity_entry.device_id).to_be_none()

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(history_stats_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )
    expect(
        history_stats_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)
    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_changes_source_entity_moved_other_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    history_stats_config_entry: MockConfigEntry = Depends(
        history_stats_config_entry_fx
    ),
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
        await hass.config_entries.async_setup(history_stats_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    history_stats_entity_entry = entity_registry.async_get("sensor.my_history_stats")
    expect(history_stats_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(history_stats_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    expect(history_stats_config_entry.entry_id in sensor_device_2.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, history_stats_entity_entry.entity_id)

    with patch(
        "homeassistant.components.history_stats.async_unload_entry",
        wraps=history_stats.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=sensor_device_2.id
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    history_stats_entity_entry = entity_registry.async_get("sensor.my_history_stats")
    expect(history_stats_entity_entry.device_id).to_equal(sensor_device_2.id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(history_stats_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    expect(history_stats_config_entry.entry_id in sensor_device_2.config_entries).to_be(
        False
    )
    expect(
        history_stats_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)
    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_new_entity_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    history_stats_config_entry: MockConfigEntry = Depends(
        history_stats_config_entry_fx
    ),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the source entity's entity ID is changed."""
    expect(
        await hass.config_entries.async_setup(history_stats_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    history_stats_entity_entry = entity_registry.async_get("sensor.my_history_stats")
    expect(history_stats_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(history_stats_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, history_stats_entity_entry.entity_id)

    with patch(
        "homeassistant.components.history_stats.async_unload_entry",
        wraps=history_stats.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, new_entity_id="sensor.new_entity_id"
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    expect(history_stats_config_entry.options[CONF_ENTITY_ID]).to_equal(
        "sensor.new_entity_id"
    )

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(history_stats_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )
    expect(
        history_stats_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)
    expect(events).to_equal([])


@test
async def migration_1_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
) -> None:
    """Test migration from v1.1 removes history_stats config entry from device."""
    history_stats_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: sensor_entity_entry.entity_id,
            CONF_STATE: ["on"],
            CONF_TYPE: "count",
            CONF_START: "{{ as_timestamp(utcnow()) - 3600 }}",
            CONF_END: "{{ utcnow() }}",
        },
        title="My history stats",
        version=1,
        minor_version=1,
    )
    history_stats_config_entry.add_to_hass(hass)

    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=history_stats_config_entry.entry_id
    )

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(history_stats_config_entry.entry_id in sensor_device.config_entries).to_be(
        True
    )

    await hass.config_entries.async_setup(history_stats_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(history_stats_config_entry.state).to_be(ConfigEntryState.LOADED)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(history_stats_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )
    history_stats_entity_entry = entity_registry.async_get("sensor.my_history_stats")
    expect(history_stats_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    expect(history_stats_config_entry.version).to_equal(1)
    expect(history_stats_config_entry.minor_version).to_equal(
        HistoryStatsConfigFlowHandler.MINOR_VERSION
    )


@test
async def migration_1_2(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
) -> None:
    """Test migration from v1.2 sets state_class to measurement."""
    history_stats_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: sensor_entity_entry.entity_id,
            CONF_STATE: ["on"],
            CONF_TYPE: "count",
            CONF_START: "{{ as_timestamp(utcnow()) - 3600 }}",
            CONF_END: "{{ utcnow() }}",
        },
        title="My history stats",
        version=1,
        minor_version=2,
    )
    history_stats_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(history_stats_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(history_stats_config_entry.state).to_be(ConfigEntryState.LOADED)

    expect(history_stats_config_entry.options.get(CONF_STATE_CLASS)).to_equal(
        SensorStateClass.MEASUREMENT
    )
    expect(history_stats_config_entry.version).to_equal(1)
    expect(history_stats_config_entry.minor_version).to_equal(
        HistoryStatsConfigFlowHandler.MINOR_VERSION
    )

    expect(hass.states.get("sensor.my_history_stats")).not_.to_be_none()
    expect(
        hass.states.get("sensor.my_history_stats").attributes.get(CONF_STATE_CLASS)
    ).to_equal(SensorStateClass.MEASUREMENT)


@test
async def migration_from_future_version(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test migration from future version."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: "sensor.test",
            CONF_STATE: ["on"],
            CONF_TYPE: "count",
            CONF_START: "{{ as_timestamp(utcnow()) - 3600 }}",
            CONF_END: "{{ utcnow() }}",
        },
        title="My history stats",
        version=2,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
