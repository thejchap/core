"""Test the Derivative integration."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components import derivative
from homeassistant.components.derivative.const import DOMAIN
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_entity_registry_updated_event

from tests.common import MockConfigEntry
from tests.components.derivative._fixtures import (
    derivative_config_entry as derivative_config_entry_fx,
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
    derivative_entity_id = "sensor.my_derivative"

    hass.states.async_set(
        input_sensor_entity_id, "10.0", {"unit_of_measurement": "dog"}
    )
    await hass.async_block_till_done()

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My derivative",
            "round": 1.0,
            "source": "sensor.input",
            "time_window": {"seconds": 0.0},
            "unit_prefix": "k",
            "unit_time": "min",
        },
        title="My derivative",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(entity_registry.async_get(derivative_entity_id) is not None).to_be(True)

    state = hass.states.get(derivative_entity_id)
    expect(state.state).to_equal("0.0")
    expect(state.attributes["unit_of_measurement"]).to_equal("kdog/min")
    expect(state.attributes["source"]).to_equal("sensor.input")

    hass.states.async_set(input_sensor_entity_id, 10, {"unit_of_measurement": "dog"})
    hass.states.async_set(input_sensor_entity_id, 11, {"unit_of_measurement": "dog"})
    await hass.async_block_till_done()
    state = hass.states.get(derivative_entity_id)
    expect(state.state).not_.to_equal("0")
    expect(state.attributes["unit_of_measurement"]).to_equal("kdog/min")

    # Remove the config entry
    expect(
        await hass.config_entries.async_remove(config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(hass.states.get(derivative_entity_id)).to_be_none()
    expect(entity_registry.async_get(derivative_entity_id)).to_be_none()


@test
async def async_handle_source_entity_changes_source_entity_removed(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    derivative_config_entry: MockConfigEntry = Depends(derivative_config_entry_fx),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the derivative config entry is removed when the source entity is removed."""
    expect(
        await hass.config_entries.async_setup(derivative_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    derivative_entity_entry = entity_registry.async_get("sensor.my_derivative")
    expect(derivative_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(derivative_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, derivative_entity_entry.entity_id)

    # Remove the source sensor's config entry from the device, this removes the
    # source sensor
    with patch(
        "homeassistant.components.derivative.async_unload_entry",
        wraps=derivative.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_not_called()

    derivative_entity_entry = entity_registry.async_get("sensor.my_derivative")
    expect(derivative_entity_entry.device_id).to_be_none()

    expect(device_registry.async_get(sensor_device.id)).to_be_falsy()

    expect(
        derivative_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_changes_source_entity_removed_shared_device(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    derivative_config_entry: MockConfigEntry = Depends(derivative_config_entry_fx),
    sensor_config_entry: ConfigEntry = Depends(sensor_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the derivative config entry is removed when the source entity is removed."""
    # Add another config entry to the sensor device
    other_config_entry = MockConfigEntry()
    other_config_entry.add_to_hass(hass)
    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=other_config_entry.entry_id
    )

    expect(
        await hass.config_entries.async_setup(derivative_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    derivative_entity_entry = entity_registry.async_get("sensor.my_derivative")
    expect(derivative_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(derivative_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, derivative_entity_entry.entity_id)

    with patch(
        "homeassistant.components.derivative.async_unload_entry",
        wraps=derivative.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_not_called()

    derivative_entity_entry = entity_registry.async_get("sensor.my_derivative")
    expect(derivative_entity_entry.device_id).to_be_none()

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(derivative_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    expect(
        derivative_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_changes_source_entity_removed_from_device(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    derivative_config_entry: MockConfigEntry = Depends(derivative_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the source entity removed from the source device."""
    expect(
        await hass.config_entries.async_setup(derivative_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    derivative_entity_entry = entity_registry.async_get("sensor.my_derivative")
    expect(derivative_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(derivative_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, derivative_entity_entry.entity_id)

    with patch(
        "homeassistant.components.derivative.async_unload_entry",
        wraps=derivative.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=None
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    derivative_entity_entry = entity_registry.async_get("sensor.my_derivative")
    expect(derivative_entity_entry.device_id).to_be_none()

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(derivative_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    expect(
        derivative_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_changes_source_entity_moved_other_device(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    derivative_config_entry: MockConfigEntry = Depends(derivative_config_entry_fx),
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
        await hass.config_entries.async_setup(derivative_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    derivative_entity_entry = entity_registry.async_get("sensor.my_derivative")
    expect(derivative_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(derivative_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    expect(derivative_config_entry.entry_id in sensor_device_2.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, derivative_entity_entry.entity_id)

    with patch(
        "homeassistant.components.derivative.async_unload_entry",
        wraps=derivative.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=sensor_device_2.id
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    derivative_entity_entry = entity_registry.async_get("sensor.my_derivative")
    expect(derivative_entity_entry.device_id).to_equal(sensor_device_2.id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(derivative_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    expect(derivative_config_entry.entry_id in sensor_device_2.config_entries).to_be(
        False
    )

    expect(
        derivative_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal(["update"])


@test
async def async_handle_source_entity_new_entity_id(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    derivative_config_entry: MockConfigEntry = Depends(derivative_config_entry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test the source entity's entity ID is changed."""
    expect(
        await hass.config_entries.async_setup(derivative_config_entry.entry_id)
    ).to_be_truthy()
    await hass.async_block_till_done()

    derivative_entity_entry = entity_registry.async_get("sensor.my_derivative")
    expect(derivative_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(derivative_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    events = track_entity_registry_actions(hass, derivative_entity_entry.entity_id)

    with patch(
        "homeassistant.components.derivative.async_unload_entry",
        wraps=derivative.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, new_entity_id="sensor.new_entity_id"
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    expect(derivative_config_entry.options["source"]).to_equal("sensor.new_entity_id")

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(derivative_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )

    expect(
        derivative_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    expect(events).to_equal([])


@test.cases(
    test.case("empty", unit_prefix={}, expect_prefix=None),
    test.case("k", unit_prefix={"unit_prefix": "k"}, expect_prefix="k"),
    test.case("none", unit_prefix={"unit_prefix": "none"}, expect_prefix=None),
)
async def migration_1_1(
    unit_prefix: dict,
    expect_prefix: str | None,
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test migration from v1.1 deletes "none" unit_prefix."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My derivative",
            "round": 1.0,
            "source": "sensor.power",
            "time_window": {"seconds": 0.0},
            **unit_prefix,
            "unit_time": "min",
        },
        title="My derivative",
        version=1,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.options["unit_time"]).to_equal("min")
    expect(config_entry.options.get("unit_prefix")).to_equal(expect_prefix)

    expect(config_entry.version).to_equal(1)
    expect(config_entry.minor_version).to_equal(4)


@test
async def migration_1_2(
    hass: HomeAssistant = Depends(hass_fx),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    sensor_device: dr.DeviceEntry = Depends(sensor_device_fx),
    sensor_entity_entry: er.RegistryEntry = Depends(sensor_entity_entry_fx),
) -> None:
    """Test migration from v1.2 removes derivative config entry from device."""
    derivative_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My derivative",
            "round": 1.0,
            "source": "sensor.test_unique",
            "time_window": {"seconds": 0.0},
            "unit_prefix": "k",
            "unit_time": "min",
        },
        title="My derivative",
        version=1,
        minor_version=2,
    )
    derivative_config_entry.add_to_hass(hass)

    # Add the helper config entry to the device
    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=derivative_config_entry.entry_id
    )

    # Check preconditions
    sensor_device = device_registry.async_get(sensor_device.id)
    expect(derivative_config_entry.entry_id in sensor_device.config_entries).to_be(
        True
    )

    await hass.config_entries.async_setup(derivative_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(derivative_config_entry.state).to_be(ConfigEntryState.LOADED)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(derivative_config_entry.entry_id in sensor_device.config_entries).to_be(
        False
    )
    derivative_entity_entry = entity_registry.async_get("sensor.my_derivative")
    expect(derivative_entity_entry.device_id).to_equal(sensor_entity_entry.device_id)

    expect(derivative_config_entry.version).to_equal(1)
    expect(derivative_config_entry.minor_version).to_equal(4)


@test.cases(
    test.case(
        "micro_sign",
        unit_prefix={"unit_prefix": "µ"},
        expect_prefix="μ",
    ),
    test.case(
        "greek_mu",
        unit_prefix={"unit_prefix": "μ"},
        expect_prefix="μ",
    ),
)
async def migration_1_4(
    unit_prefix: dict,
    expect_prefix: str,
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test migration from v1.4 migrates to Greek Mu char" unit_prefix."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My derivative",
            "round": 1.0,
            "source": "sensor.power",
            "time_window": {"seconds": 0.0},
            **unit_prefix,
            "unit_time": "min",
        },
        title="My derivative",
        version=1,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.options["unit_time"]).to_equal("min")
    expect(config_entry.options.get("unit_prefix")).to_equal(expect_prefix)

    expect(config_entry.version).to_equal(1)
    expect(config_entry.minor_version).to_equal(4)


@test
async def migration_from_future_version(
    hass: HomeAssistant = Depends(hass_fx),
) -> None:
    """Test migration from future version."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My derivative",
            "round": 1.0,
            "source": "sensor.power",
            "time_window": {"seconds": 0.0},
            "unit_prefix": "k",
            "unit_time": "min",
        },
        title="My derivative",
        version=2,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
