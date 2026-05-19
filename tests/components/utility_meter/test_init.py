"""The tests for the utility_meter component."""

from datetime import timedelta
from unittest.mock import patch

from freezegun import freeze_time
from tryke import Depends, expect, fixture, test

from homeassistant.components import utility_meter
from homeassistant.components.select import (
    ATTR_OPTION,
    DOMAIN as SELECT_DOMAIN,
    SERVICE_SELECT_OPTION,
)
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.components.utility_meter import (
    select as um_select,
    sensor as um_sensor,
)
from homeassistant.components.utility_meter.config_flow import ConfigFlowHandler
from homeassistant.components.utility_meter.const import DOMAIN, SERVICE_RESET
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_UNIT_OF_MEASUREMENT,
    CONF_PLATFORM,
    EVENT_HOMEASSISTANT_START,
    UnitOfEnergy,
)
from homeassistant.core import Event, HomeAssistant, State, callback
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.event import async_track_entity_registry_updated_event
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import MockConfigEntry, mock_restore_cache
from tests.hass_fixtures import (
    device_registry as device_registry_fx,
    entity_registry as entity_registry_fx,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


def _track_entity_registry_actions(hass: HomeAssistant, entity_id: str) -> list[str]:
    """Track entity registry actions for an entity."""
    events: list[str] = []

    @callback
    def add_event(event: Event[er.EventEntityRegistryUpdatedData]) -> None:
        """Add entity registry updated event to the list."""
        events.append(event.data["action"])

    async_track_entity_registry_updated_event(hass, entity_id, add_event)

    return events


def _make_sensor_entity_entry(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    entity_registry: er.EntityRegistry,
) -> tuple[MockConfigEntry, dr.DeviceEntry, er.RegistryEntry]:
    """Create a sensor config entry, device, and entity in one shot."""
    sensor_config_entry = MockConfigEntry()
    sensor_config_entry.add_to_hass(hass)
    sensor_device = device_registry.async_get_or_create(
        config_entry_id=sensor_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    sensor_entity_entry = entity_registry.async_get_or_create(
        "sensor",
        "test",
        "unique",
        config_entry=sensor_config_entry,
        device_id=sensor_device.id,
        original_name="ABC",
    )
    return sensor_config_entry, sensor_device, sensor_entity_entry


def _make_utility_meter_config_entry(
    hass: HomeAssistant,
    source_entity_id: str,
    tariffs: list[str],
) -> MockConfigEntry:
    """Create a utility_meter config entry."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "My utility meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": source_entity_id,
            "tariffs": tariffs,
        },
        title="My utility meter",
        version=ConfigFlowHandler.VERSION,
        minor_version=ConfigFlowHandler.MINOR_VERSION,
    )
    config_entry.add_to_hass(hass)
    return config_entry


@test
async def restore_state(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test utility sensor restore state."""
    config = {
        "utility_meter": {
            "energy_bill": {
                "source": "sensor.energy",
                "tariffs": ["onpeak", "midpeak", "offpeak"],
            }
        }
    }
    mock_restore_cache(
        hass,
        [
            State(
                "select.energy_bill",
                "midpeak",
            ),
        ],
    )

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    expect(await async_setup_component(hass, SENSOR_DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    state = hass.states.get("select.energy_bill")
    expect(state.state).to_equal("midpeak")


@test.cases(
    test.case("list_meter", meter=["select.energy_bill"]),
    test.case("str_meter", meter="select.energy_bill"),
)
async def services(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    meter: list[str] | str,
) -> None:
    """Test energy sensor reset service."""
    config = {
        "utility_meter": {
            "energy_bill": {
                "source": "sensor.energy",
                "cycle": "hourly",
                "tariffs": ["peak", "offpeak"],
            },
            "energy_bill2": {
                "source": "sensor.energy",
                "cycle": "hourly",
                "tariffs": ["peak", "offpeak"],
            },
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    expect(await async_setup_component(hass, SENSOR_DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    entity_id = config[DOMAIN]["energy_bill"]["source"]
    hass.states.async_set(
        entity_id, 1, {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR}
    )
    await hass.async_block_till_done()

    now = dt_util.utcnow() + timedelta(seconds=10)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            3,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    expect(hass.states.get("sensor.energy_bill_peak").state).to_equal("2")
    expect(hass.states.get("sensor.energy_bill_offpeak").state).to_equal("0")

    # Change tariff
    data = {ATTR_ENTITY_ID: "select.energy_bill", ATTR_OPTION: "offpeak"}
    await hass.services.async_call(SELECT_DOMAIN, SERVICE_SELECT_OPTION, data)
    await hass.async_block_till_done()

    now += timedelta(seconds=10)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            4,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    expect(hass.states.get("sensor.energy_bill_peak").state).to_equal("2")
    expect(hass.states.get("sensor.energy_bill_offpeak").state).to_equal("1")

    # Change tariff - invalid
    data = {ATTR_ENTITY_ID: "select.energy_bill", "option": "wrong_tariff"}
    await hass.services.async_call(SELECT_DOMAIN, SERVICE_SELECT_OPTION, data)
    await hass.async_block_till_done()

    expect(hass.states.get("select.energy_bill").state != "wrong_tariff").to_be(True)

    data = {ATTR_ENTITY_ID: "select.energy_bill", "option": "peak"}
    await hass.services.async_call(SELECT_DOMAIN, SERVICE_SELECT_OPTION, data)
    await hass.async_block_till_done()

    now += timedelta(seconds=10)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            5,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    expect(hass.states.get("sensor.energy_bill_peak").state).to_equal("3")
    expect(hass.states.get("sensor.energy_bill_offpeak").state).to_equal("1")

    # Reset meters
    data = {ATTR_ENTITY_ID: meter}
    await hass.services.async_call(DOMAIN, SERVICE_RESET, data)
    await hass.async_block_till_done()

    expect(hass.states.get("sensor.energy_bill_peak").state).to_equal("0")
    expect(hass.states.get("sensor.energy_bill_offpeak").state).to_equal("0")

    # meanwhile energy_bill2_peak accumulated all kWh
    expect(hass.states.get("sensor.energy_bill2_peak").state).to_equal("4")


@test
async def services_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test energy sensor reset service."""
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "Energy bill",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": "sensor.energy",
            "tariffs": ["peak", "offpeak"],
        },
        title="Energy bill",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "Energy bill2",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": "sensor.energy",
            "tariffs": ["peak", "offpeak"],
        },
        title="Energy bill2",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    hass.bus.async_fire(EVENT_HOMEASSISTANT_START)
    entity_id = "sensor.energy"
    hass.states.async_set(
        entity_id, 1, {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR}
    )
    await hass.async_block_till_done()

    now = dt_util.utcnow() + timedelta(seconds=10)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            3,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    expect(hass.states.get("sensor.energy_bill_peak").state).to_equal("2")
    expect(hass.states.get("sensor.energy_bill_offpeak").state).to_equal("0")

    data = {ATTR_ENTITY_ID: "select.energy_bill", "option": "offpeak"}
    await hass.services.async_call(SELECT_DOMAIN, SERVICE_SELECT_OPTION, data)
    await hass.async_block_till_done()

    now += timedelta(seconds=10)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            4,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    expect(hass.states.get("sensor.energy_bill_peak").state).to_equal("2")
    expect(hass.states.get("sensor.energy_bill_offpeak").state).to_equal("1")

    data = {ATTR_ENTITY_ID: "select.energy_bill", "option": "wrong_tariff"}
    await hass.services.async_call(SELECT_DOMAIN, SERVICE_SELECT_OPTION, data)
    await hass.async_block_till_done()

    expect(hass.states.get("select.energy_bill").state != "wrong_tariff").to_be(True)

    data = {ATTR_ENTITY_ID: "select.energy_bill", "option": "peak"}
    await hass.services.async_call(SELECT_DOMAIN, SERVICE_SELECT_OPTION, data)
    await hass.async_block_till_done()

    now += timedelta(seconds=10)
    with freeze_time(now):
        hass.states.async_set(
            entity_id,
            5,
            {ATTR_UNIT_OF_MEASUREMENT: UnitOfEnergy.KILO_WATT_HOUR},
            force_update=True,
        )
        await hass.async_block_till_done()

    expect(hass.states.get("sensor.energy_bill_peak").state).to_equal("3")
    expect(hass.states.get("sensor.energy_bill_offpeak").state).to_equal("1")

    data = {ATTR_ENTITY_ID: "select.energy_bill"}
    await hass.services.async_call(DOMAIN, SERVICE_RESET, data)
    await hass.async_block_till_done()

    expect(hass.states.get("sensor.energy_bill_peak").state).to_equal("0")
    expect(hass.states.get("sensor.energy_bill_offpeak").state).to_equal("0")

    expect(hass.states.get("sensor.energy_bill2_peak").state).to_equal("4")


@test
async def cron(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test cron pattern."""
    config = {
        "utility_meter": {
            "energy_bill": {
                "source": "sensor.energy",
                "cron": "*/5 * * * *",
            }
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)


@test
async def cron_and_meter(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test cron pattern and meter type fails."""
    config = {
        "utility_meter": {
            "energy_bill": {
                "source": "sensor.energy",
                "cycle": "hourly",
                "cron": "0 0 1 * *",
            }
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(False)


@test
async def both_cron_and_meter(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test cron pattern and meter type passes in different meter."""
    config = {
        "utility_meter": {
            "energy_bill": {
                "source": "sensor.energy",
                "cron": "0 0 1 * *",
            },
            "water_bill": {
                "source": "sensor.water",
                "cycle": "hourly",
            },
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(True)
    await hass.async_block_till_done()


@test
async def cron_and_offset(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test cron pattern and offset fails."""
    config = {
        "utility_meter": {
            "energy_bill": {
                "source": "sensor.energy",
                "offset": {"days": 1},
                "cron": "0 0 1 * *",
            }
        }
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(False)


@test
async def bad_cron(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test bad cron pattern."""
    config = {
        "utility_meter": {"energy_bill": {"source": "sensor.energy", "cron": "*"}}
    }

    expect(await async_setup_component(hass, DOMAIN, config)).to_be(False)


@test
async def setup_missing_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test setup with configuration missing discovery_info."""
    expect(
        await um_select.async_setup_platform(hass, {CONF_PLATFORM: DOMAIN}, None)
    ).to_be(None)
    expect(
        await um_sensor.async_setup_platform(hass, {CONF_PLATFORM: DOMAIN}, None)
    ).to_be(None)


@test.cases(
    test.case("no_tariffs", tariffs=[], expected_entities=["sensor.electricity_meter"]),
    test.case(
        "with_tariffs",
        tariffs=["high", "low"],
        expected_entities=[
            "sensor.electricity_meter_low",
            "sensor.electricity_meter_high",
            "select.electricity_meter",
        ],
    ),
)
async def setup_and_remove_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    *,
    tariffs: list[str],
    expected_entities: list[str],
) -> None:
    """Test setting up and removing a config entry."""
    input_sensor_entity_id = "sensor.input"

    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": input_sensor_entity_id,
            "tariffs": tariffs,
        },
        title="Electricity meter",
    )
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(len(expected_entities))
    expect(len(entity_registry.entities)).to_equal(len(expected_entities))
    for entity in expected_entities:
        expect(hass.states.get(entity) is not None).to_be(True)
        expect(entity in entity_registry.entities).to_be(True)

    expect(await hass.config_entries.async_remove(config_entry.entry_id)).to_be_truthy()
    await hass.async_block_till_done()

    expect(len(hass.states.async_all())).to_equal(0)
    expect(len(entity_registry.entities)).to_equal(0)


@test.cases(
    test.case("no_tariffs", tariffs=[], expected_entities={"sensor.my_utility_meter"}),
    test.case(
        "with_tariffs",
        tariffs=["peak", "offpeak"],
        expected_entities={
            "select.my_utility_meter",
            "sensor.my_utility_meter_offpeak",
            "sensor.my_utility_meter_peak",
        },
    ),
)
async def async_handle_source_entity_changes_source_entity_removed(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    *,
    tariffs: list[str],
    expected_entities: set[str],
) -> None:
    """Test the utility_meter config entry is removed when the source entity is removed."""
    sensor_config_entry, sensor_device, sensor_entity_entry = _make_sensor_entity_entry(
        hass, device_registry, entity_registry
    )
    utility_meter_config_entry = _make_utility_meter_config_entry(
        hass, sensor_entity_entry.entity_id, tariffs
    )

    expect(
        await hass.config_entries.async_setup(utility_meter_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    events: dict[str, list[str]] = {}
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_equal(sensor_entity_entry.device_id)
        events[utility_meter_entity.entity_id] = _track_entity_registry_actions(
            hass, utility_meter_entity.entity_id
        )
    expect(set(events)).to_equal(expected_entities)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(
        utility_meter_config_entry.entry_id not in sensor_device.config_entries
    ).to_be(True)

    with patch(
        "homeassistant.components.utility_meter.async_unload_entry",
        wraps=utility_meter.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_not_called()

    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_be(None)

    expect(device_registry.async_get(sensor_device.id)).to_be(None)

    expect(
        utility_meter_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    for entity_events in events.values():
        expect(entity_events).to_equal(["update"])


@test.cases(
    test.case("no_tariffs", tariffs=[], expected_entities={"sensor.my_utility_meter"}),
    test.case(
        "with_tariffs",
        tariffs=["peak", "offpeak"],
        expected_entities={
            "select.my_utility_meter",
            "sensor.my_utility_meter_offpeak",
            "sensor.my_utility_meter_peak",
        },
    ),
)
async def async_handle_source_entity_changes_source_entity_removed_shared_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    *,
    tariffs: list[str],
    expected_entities: set[str],
) -> None:
    """Test the utility_meter config entry is removed when the source entity is removed."""
    sensor_config_entry, sensor_device, sensor_entity_entry = _make_sensor_entity_entry(
        hass, device_registry, entity_registry
    )
    utility_meter_config_entry = _make_utility_meter_config_entry(
        hass, sensor_entity_entry.entity_id, tariffs
    )

    other_config_entry = MockConfigEntry()
    other_config_entry.add_to_hass(hass)
    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=other_config_entry.entry_id
    )

    expect(
        await hass.config_entries.async_setup(utility_meter_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    events: dict[str, list[str]] = {}
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_equal(sensor_entity_entry.device_id)
        events[utility_meter_entity.entity_id] = _track_entity_registry_actions(
            hass, utility_meter_entity.entity_id
        )
    expect(set(events)).to_equal(expected_entities)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(
        utility_meter_config_entry.entry_id not in sensor_device.config_entries
    ).to_be(True)

    with patch(
        "homeassistant.components.utility_meter.async_unload_entry",
        wraps=utility_meter.async_unload_entry,
    ) as mock_unload_entry:
        device_registry.async_update_device(
            sensor_device.id, remove_config_entry_id=sensor_config_entry.entry_id
        )
        await hass.async_block_till_done()
        await hass.async_block_till_done()
    mock_unload_entry.assert_not_called()

    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_be(None)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(
        utility_meter_config_entry.entry_id not in sensor_device.config_entries
    ).to_be(True)
    expect(
        utility_meter_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    for entity_events in events.values():
        expect(entity_events).to_equal(["update"])


@test.cases(
    test.case("no_tariffs", tariffs=[], expected_entities={"sensor.my_utility_meter"}),
    test.case(
        "with_tariffs",
        tariffs=["peak", "offpeak"],
        expected_entities={
            "select.my_utility_meter",
            "sensor.my_utility_meter_offpeak",
            "sensor.my_utility_meter_peak",
        },
    ),
)
async def async_handle_source_entity_changes_source_entity_removed_from_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    *,
    tariffs: list[str],
    expected_entities: set[str],
) -> None:
    """Test the source entity removed from the source device."""
    _, sensor_device, sensor_entity_entry = _make_sensor_entity_entry(
        hass, device_registry, entity_registry
    )
    utility_meter_config_entry = _make_utility_meter_config_entry(
        hass, sensor_entity_entry.entity_id, tariffs
    )

    expect(
        await hass.config_entries.async_setup(utility_meter_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    events: dict[str, list[str]] = {}
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_equal(sensor_entity_entry.device_id)
        events[utility_meter_entity.entity_id] = _track_entity_registry_actions(
            hass, utility_meter_entity.entity_id
        )
    expect(set(events)).to_equal(expected_entities)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(
        utility_meter_config_entry.entry_id not in sensor_device.config_entries
    ).to_be(True)

    with patch(
        "homeassistant.components.utility_meter.async_unload_entry",
        wraps=utility_meter.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=None
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_be(None)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(
        utility_meter_config_entry.entry_id not in sensor_device.config_entries
    ).to_be(True)
    expect(
        utility_meter_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    for entity_events in events.values():
        expect(entity_events).to_equal(["update"])


@test.cases(
    test.case("no_tariffs", tariffs=[], expected_entities={"sensor.my_utility_meter"}),
    test.case(
        "with_tariffs",
        tariffs=["peak", "offpeak"],
        expected_entities={
            "select.my_utility_meter",
            "sensor.my_utility_meter_offpeak",
            "sensor.my_utility_meter_peak",
        },
    ),
)
async def async_handle_source_entity_changes_source_entity_moved_other_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    *,
    tariffs: list[str],
    expected_entities: set[str],
) -> None:
    """Test the source entity is moved to another device."""
    sensor_config_entry, sensor_device, sensor_entity_entry = _make_sensor_entity_entry(
        hass, device_registry, entity_registry
    )
    utility_meter_config_entry = _make_utility_meter_config_entry(
        hass, sensor_entity_entry.entity_id, tariffs
    )

    sensor_device_2 = device_registry.async_get_or_create(
        config_entry_id=sensor_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:FF")},
    )

    expect(
        await hass.config_entries.async_setup(utility_meter_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    events: dict[str, list[str]] = {}
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_equal(sensor_entity_entry.device_id)
        events[utility_meter_entity.entity_id] = _track_entity_registry_actions(
            hass, utility_meter_entity.entity_id
        )
    expect(set(events)).to_equal(expected_entities)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(
        utility_meter_config_entry.entry_id not in sensor_device.config_entries
    ).to_be(True)
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    expect(
        utility_meter_config_entry.entry_id not in sensor_device_2.config_entries
    ).to_be(True)

    with patch(
        "homeassistant.components.utility_meter.async_unload_entry",
        wraps=utility_meter.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, device_id=sensor_device_2.id
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_equal(sensor_device_2.id)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(
        utility_meter_config_entry.entry_id not in sensor_device.config_entries
    ).to_be(True)
    sensor_device_2 = device_registry.async_get(sensor_device_2.id)
    expect(
        utility_meter_config_entry.entry_id not in sensor_device_2.config_entries
    ).to_be(True)
    expect(
        utility_meter_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    for entity_events in events.values():
        expect(entity_events).to_equal(["update"])


@test.cases(
    test.case("no_tariffs", tariffs=[], expected_entities={"sensor.my_utility_meter"}),
    test.case(
        "with_tariffs",
        tariffs=["peak", "offpeak"],
        expected_entities={
            "select.my_utility_meter",
            "sensor.my_utility_meter_offpeak",
            "sensor.my_utility_meter_peak",
        },
    ),
)
async def async_handle_source_entity_new_entity_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    *,
    tariffs: list[str],
    expected_entities: set[str],
) -> None:
    """Test the source entity's entity ID is changed."""
    _, sensor_device, sensor_entity_entry = _make_sensor_entity_entry(
        hass, device_registry, entity_registry
    )
    utility_meter_config_entry = _make_utility_meter_config_entry(
        hass, sensor_entity_entry.entity_id, tariffs
    )

    expect(
        await hass.config_entries.async_setup(utility_meter_config_entry.entry_id)
    ).to_be(True)
    await hass.async_block_till_done()

    events: dict[str, list[str]] = {}
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        expect(utility_meter_entity.device_id).to_equal(sensor_entity_entry.device_id)
        events[utility_meter_entity.entity_id] = _track_entity_registry_actions(
            hass, utility_meter_entity.entity_id
        )
    expect(set(events)).to_equal(expected_entities)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(
        utility_meter_config_entry.entry_id not in sensor_device.config_entries
    ).to_be(True)

    with patch(
        "homeassistant.components.utility_meter.async_unload_entry",
        wraps=utility_meter.async_unload_entry,
    ) as mock_unload_entry:
        entity_registry.async_update_entity(
            sensor_entity_entry.entity_id, new_entity_id="sensor.new_entity_id"
        )
        await hass.async_block_till_done()
    mock_unload_entry.assert_called_once()

    expect(utility_meter_config_entry.options["source"]).to_equal(
        "sensor.new_entity_id"
    )

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(
        utility_meter_config_entry.entry_id not in sensor_device.config_entries
    ).to_be(True)
    expect(
        utility_meter_config_entry.entry_id in hass.config_entries.async_entry_ids()
    ).to_be(True)

    for entity_events in events.values():
        expect(entity_events).to_equal([])


@test.cases(
    test.case("no_tariffs", tariffs=[], expected_entities={"sensor.my_utility_meter"}),
    test.case(
        "with_tariffs",
        tariffs=["peak", "offpeak"],
        expected_entities={
            "select.my_utility_meter",
            "sensor.my_utility_meter_offpeak",
            "sensor.my_utility_meter_peak",
        },
    ),
)
async def migration_2_1(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fx),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fx),
    *,
    tariffs: list[str],
    expected_entities: set[str],
) -> None:
    """Test migration from v2.1 removes utility_meter config entry from device."""
    _, sensor_device, sensor_entity_entry = _make_sensor_entity_entry(
        hass, device_registry, entity_registry
    )

    utility_meter_config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "My utility meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": sensor_entity_entry.entity_id,
            "tariffs": tariffs,
        },
        title="My utility meter",
        version=2,
        minor_version=1,
    )
    utility_meter_config_entry.add_to_hass(hass)

    device_registry.async_update_device(
        sensor_device.id, add_config_entry_id=utility_meter_config_entry.entry_id
    )

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(
        utility_meter_config_entry.entry_id in sensor_device.config_entries
    ).to_be(True)

    await hass.config_entries.async_setup(utility_meter_config_entry.entry_id)
    await hass.async_block_till_done()

    expect(utility_meter_config_entry.state).to_be(ConfigEntryState.LOADED)

    sensor_device = device_registry.async_get(sensor_device.id)
    expect(
        utility_meter_config_entry.entry_id not in sensor_device.config_entries
    ).to_be(True)

    entities: set[str] = set()
    for (
        utility_meter_entity
    ) in entity_registry.entities.get_entries_for_config_entry_id(
        utility_meter_config_entry.entry_id
    ):
        entities.add(utility_meter_entity.entity_id)
        expect(utility_meter_entity.device_id).to_equal(sensor_entity_entry.device_id)
    expect(entities).to_equal(expected_entities)

    expect(utility_meter_config_entry.version).to_equal(2)
    expect(utility_meter_config_entry.minor_version).to_equal(2)


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
            "cycle": "monthly",
            "delta_values": False,
            "name": "My utility meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": "sensor.test",
            "tariffs": [],
        },
        title="My utility meter",
        version=3,
        minor_version=1,
    )
    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    expect(config_entry.state).to_be(ConfigEntryState.MIGRATION_ERROR)
