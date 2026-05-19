"""Test Statistics component setup process."""

from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import statistics
from homeassistant.components.statistics import DOMAIN
from homeassistant.components.statistics.config_flow import StatisticsConfigFlowHandler
from homeassistant.components.statistics.sensor import (
    CONF_KEEP_LAST_SAMPLE,
    CONF_MAX_AGE,
    CONF_PERCENTILE,
    CONF_PRECISION,
    CONF_SAMPLES_MAX_BUFFER_SIZE,
    CONF_STATE_CHARACTERISTIC,
    DEFAULT_NAME,
    STAT_AVERAGE_LINEAR,
)
from homeassistant.config_entries import (
    SOURCE_USER,
    ConfigEntry,
    ConfigEntryState,
)
from homeassistant.const import (
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_ENTITY_ID,
    CONF_NAME,
    UnitOfTemperature,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_entity_registry_updated_event

from ._fixtures import recorder_mock

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)

VALUES_NUMERIC = [17, 20, 15.2, 5, 3.8, 9.2, 6.7, 14, 6]


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _recorder: object = Depends(recorder_mock),
) -> None:
    """Force tryke fixture resolution before each test."""
    print("DEBUG _trigger_executor invoked")


@fixture
def sensor_config_entry(
    hass: HomeAssistant = Depends(hass_fixture),
) -> MockConfigEntry:
    """Fixture to create a sensor config entry."""
    sensor_config_entry = MockConfigEntry()
    sensor_config_entry.add_to_hass(hass)
    return sensor_config_entry


@fixture
def sensor_device(
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry),
) -> dr.DeviceEntry:
    """Fixture to create a sensor device."""
    return device_registry.async_get_or_create(
        config_entry_id=sensor_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )


@fixture
def sensor_entity_entry(
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry),
    sensor_device: dr.DeviceEntry = Depends(sensor_device),
) -> er.RegistryEntry:
    """Fixture to create a sensor entity entry."""
    return entity_registry.async_get_or_create(
        "sensor",
        "test",
        "unique",
        config_entry=sensor_config_entry,
        device_id=sensor_device.id,
        original_name="ABC",
    )


@fixture
def statistics_config_entry(
    _network: None = Depends(mock_network),
    _recorder: object = Depends(recorder_mock),
    hass: HomeAssistant = Depends(hass_fixture),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry),
) -> MockConfigEntry:
    """Fixture to create a statistics config entry."""
    import traceback
    orig_setup = statistics.async_setup_entry
    async def traced_setup(hass_, entry_):
        print(f"DEBUG async_setup_entry called for {entry_.entry_id}", flush=True)
        traceback.print_stack()
        return await orig_setup(hass_, entry_)
    p = patch("homeassistant.components.statistics.async_setup_entry", new=traced_setup)
    p.start()
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My statistics",
            "entity_id": sensor_entity_entry.entity_id,
            "state_characteristic": "mean",
            "keep_last_sample": False,
            "percentile": 50.0,
            "precision": 2.0,
            "sampling_size": 20.0,
        },
        title="My statistics",
        version=StatisticsConfigFlowHandler.VERSION,
        minor_version=StatisticsConfigFlowHandler.MINOR_VERSION,
    )
    print(f"DEBUG fixture state after init: {config_entry.state}")
    config_entry.add_to_hass(hass)
    print(f"DEBUG fixture state after add_to_hass: {config_entry.state}")

    return config_entry


@fixture
def get_config() -> dict[str, Any]:
    """Return the default config used by ``loaded_entry``."""
    return {
        CONF_NAME: DEFAULT_NAME,
        CONF_ENTITY_ID: "sensor.test_monitored",
        CONF_STATE_CHARACTERISTIC: STAT_AVERAGE_LINEAR,
        CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0,
        CONF_MAX_AGE: {"hours": 8, "minutes": 5, "seconds": 5},
        CONF_KEEP_LAST_SAMPLE: False,
        CONF_PERCENTILE: 50.0,
        CONF_PRECISION: 2.0,
    }


@fixture
async def loaded_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    get_config: dict[str, Any] = Depends(get_config),
) -> MockConfigEntry:
    """Set up the Statistics integration in Home Assistant."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        source=SOURCE_USER,
        options=get_config,
        entry_id="1",
    )

    config_entry.add_to_hass(hass)

    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    for value in VALUES_NUMERIC:
        hass.states.async_set(
            "sensor.test_monitored",
            str(value),
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
        )
    await hass.async_block_till_done()

    return config_entry


def track_entity_registry_actions(hass: HomeAssistant, entity_id: str) -> list[str]:
    """Track entity registry actions for an entity."""
    events: list[str] = []

    @callback
    def add_event(event: Event[er.EventEntityRegistryUpdatedData]) -> None:
        events.append(event.data["action"])

    async_track_entity_registry_updated_event(hass, entity_id, add_event)

    return events


@test
async def unload_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    loaded_entry: MockConfigEntry = Depends(loaded_entry),
) -> None:
    """Test unload an entry."""
    expect(loaded_entry.state).to_be(ConfigEntryState.LOADED)
    expect(await hass.config_entries.async_unload(loaded_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()
    expect(loaded_entry.state).to_be(ConfigEntryState.NOT_LOADED)


@test
async def async_handle_source_entity_changes_source_entity_removed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    statistics_config_entry: MockConfigEntry = Depends(statistics_config_entry),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry),
    sensor_device: dr.DeviceEntry = Depends(sensor_device),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry),
) -> None:
    """Test the statistics config entry is removed when the source entity is removed."""
    # Patch async_setup_entry to capture stack trace of who calls it.
    import traceback
    orig_setup = statistics.async_setup_entry
    async def traced_setup(hass_, entry_):
        print("DEBUG async_setup_entry called for", entry_.entry_id)
        traceback.print_stack()
        return await orig_setup(hass_, entry_)
    with patch(
        "homeassistant.components.statistics.async_setup_entry", new=traced_setup
    ):
        print(f"DEBUG entry state before async_setup: {statistics_config_entry.state}")
        expect(
            await hass.config_entries.async_setup(statistics_config_entry.entry_id)
        ).to_be(True)
        await hass.async_block_till_done()

    statistics_entity_entry = entity_registry.async_get("sensor.my_statistics")
    expect(statistics_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries

    events = track_entity_registry_actions(hass, statistics_entity_entry.entity_id)

    with patch(
        "homeassistant.components.statistics.async_unload_entry",
        wraps=statistics.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    assert not entity_registry.async_get("sensor.my_statistics")
    assert not device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in hass.config_entries.async_entry_ids()
    expect(events).to_equal(["remove"])


@test
async def async_handle_source_entity_changes_source_entity_removed_shared_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    statistics_config_entry: MockConfigEntry = Depends(statistics_config_entry),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry),
    sensor_device: dr.DeviceEntry = Depends(sensor_device),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry),
) -> None:
    """Test the statistics config entry is removed when the source entity is removed."""
    other_config_entry = MockConfigEntry()
    other_config_entry.add_to_hass(hass)
    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=other_config_entry.entry_id
    )

    expect(
        await hass.config_entries.async_setup(statistics_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    statistics_entity_entry = entity_registry.async_get("sensor.my_statistics")
    expect(statistics_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries

    events = track_entity_registry_actions(hass, statistics_entity_entry.entity_id)

    with patch(
        "homeassistant.components.statistics.async_unload_entry",
        wraps=statistics.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    assert not entity_registry.async_get("sensor.my_statistics")
    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries
    assert statistics_config_entry.entry_id not in hass.config_entries.async_entry_ids()
    expect(events).to_equal(["remove"])


@test
async def async_handle_source_entity_changes_source_entity_removed_from_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    statistics_config_entry: MockConfigEntry = Depends(statistics_config_entry),
    sensor_device: dr.DeviceEntry = Depends(sensor_device),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry),
) -> None:
    """Test the source entity removed from the source device."""
    expect(
        await hass.config_entries.async_setup(statistics_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    statistics_entity_entry = entity_registry.async_get("sensor.my_statistics")
    expect(statistics_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries

    events = track_entity_registry_actions(hass, statistics_entity_entry.entity_id)

    with patch(
        "homeassistant.components.statistics.async_unload_entry",
        wraps=statistics.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=None
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    statistics_entity_entry = entity_registry.async_get("sensor.my_statistics")
    assert statistics_entity_entry.device_id is None

    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries

    assert statistics_config_entry.entry_id in hass.config_entries.async_entry_ids()
    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_changes_source_entity_moved_other_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    statistics_config_entry: MockConfigEntry = Depends(statistics_config_entry),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry),
    sensor_device: dr.DeviceEntry = Depends(sensor_device),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry),
) -> None:
    """Test the source entity is moved to another device."""
    sensor_device_2 = device_registry.async_get_or_create(
        config_entry_id=sensor_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:FF")},
    )

    expect(
        await hass.config_entries.async_setup(statistics_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    statistics_entity_entry = entity_registry.async_get("sensor.my_statistics")
    expect(statistics_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    assert statistics_config_entry.entry_id not in sensor_device_2.config_entries

    events = track_entity_registry_actions(hass, statistics_entity_entry.entity_id)

    with patch(
        "homeassistant.components.statistics.async_unload_entry",
        wraps=statistics.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=sensor_device_2.id
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    statistics_entity_entry = entity_registry.async_get("sensor.my_statistics")
    expect(statistics_entity_entry.device_id).to_equal(sensor_device_2.id)

    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    assert statistics_config_entry.entry_id not in sensor_device_2.config_entries

    assert statistics_config_entry.entry_id in hass.config_entries.async_entry_ids()
    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_new_entity_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    statistics_config_entry: MockConfigEntry = Depends(statistics_config_entry),
    sensor_device: dr.DeviceEntry = Depends(sensor_device),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry),
) -> None:
    """Test the source entity's entity ID is changed."""
    expect(
        await hass.config_entries.async_setup(statistics_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    statistics_entity_entry = entity_registry.async_get("sensor.my_statistics")
    expect(statistics_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries

    events = track_entity_registry_actions(hass, statistics_entity_entry.entity_id)

    with patch(
        "homeassistant.components.statistics.async_unload_entry",
        wraps=statistics.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, new_entity_id="sensor.new_entity_id"
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    expect(statistics_config_entry.options["entity_id"]).to_equal(
        "sensor.new_entity_id"
    )

    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries

    assert statistics_config_entry.entry_id in hass.config_entries.async_entry_ids()
    expect(events).to_equal([])


@test
async def migration_1_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry),
    sensor_device: dr.DeviceEntry = Depends(sensor_device),
) -> None:
    """Test migration from v1.1 removes statistics config entry from device."""
    statistics_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My statistics",
            "entity_id": sensor_entity_entry.entity_id,
            "state_characteristic": "mean",
            "keep_last_sample": False,
            "percentile": 50.0,
            "precision": 2.0,
            "sampling_size": 20.0,
        },
        title="My statistics",
        version=1,
        minor_version=1,
    )
    statistics_config_entry.add_to_hass(hass)

    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=statistics_config_entry.entry_id
    )

    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id in sensor_device.config_entries

    await hass.config_entries.async_setup(statistics_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(statistics_config_entry.state).to_be(ConfigEntryState.LOADED)

    sensor_device = device_registry.async_get(sensor_device.id)
    assert statistics_config_entry.entry_id not in sensor_device.config_entries
    statistics_entity_entry = entity_registry.async_get("sensor.my_statistics")
    expect(statistics_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    expect(statistics_config_entry.version).to_equal(1)
    expect(statistics_config_entry.minor_version).to_equal(2)


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
            "name": "My statistics",
            "entity_id": "sensor.test",
            "state_characteristic": "mean",
            "keep_last_sample": False,
            "percentile": 50.0,
            "precision": 2.0,
            "sampling_size": 20.0,
        },
        title="My statistics",
        version=2,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
