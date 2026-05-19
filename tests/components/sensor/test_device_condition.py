"""The test for sensor device automation (tryke port)."""

from collections.abc import Generator

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant import loader
from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.sensor import (
    ATTR_STATE_CLASS,
    DOMAIN,
    SensorDeviceClass,
    SensorStateClass,
    device_condition,
)
from homeassistant.components.sensor.const import NON_NUMERIC_DEVICE_CLASSES
from homeassistant.components.sensor.device_condition import ENTITY_CONDITIONS
from homeassistant.const import CONF_PLATFORM, PERCENTAGE, STATE_UNKNOWN, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryHider
from homeassistant.setup import async_setup_component
from homeassistant.util.json import load_json

from .common import UNITS_OF_MEASUREMENT, MockSensor, get_mock_sensor_entities

from tests.common import (
    MockConfigEntry,
    async_get_device_automation_capabilities,
    async_get_device_automations,
    async_mock_service,
    setup_test_component_platform,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)


@fixture
def _condition_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture for the module."""
    return hass


@fixture
def enable_custom_integrations(
    hass: HomeAssistant = Depends(_condition_executor),
) -> Generator[None]:
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)
    yield


@fixture
def mock_sensor_entities() -> dict[str, MockSensor]:
    """Return a dict of mock sensor entities."""
    return get_mock_sensor_entities()


@test
def matches_device_classes() -> None:
    """Ensure device class constants are declared in device_condition module."""
    for device_class in SensorDeviceClass:
        if device_class in NON_NUMERIC_DEVICE_CLASSES:
            continue
        constant_name = {
            SensorDeviceClass.BATTERY: "CONF_IS_BATTERY_LEVEL",
            SensorDeviceClass.CO: "CONF_IS_CO",
            SensorDeviceClass.CO2: "CONF_IS_CO2",
            SensorDeviceClass.ENERGY_STORAGE: "CONF_IS_ENERGY",
            SensorDeviceClass.VOLUME_STORAGE: "CONF_IS_VOLUME",
        }.get(device_class, f"CONF_IS_{device_class.value.upper()}")
        expect(hasattr(device_condition, constant_name)).to_be_truthy()

        constant_value = {
            SensorDeviceClass.BATTERY: "is_battery_level",
            SensorDeviceClass.ENERGY_STORAGE: "is_energy",
            SensorDeviceClass.VOLUME_STORAGE: "is_volume",
        }.get(device_class, f"is_{device_class.value}")
        expect(getattr(device_condition, constant_name)).to_equal(constant_value)

        expect(device_class in ENTITY_CONDITIONS).to_be_truthy()
        schema_types = device_condition.CONDITION_SCHEMA.validators[0].schema[
            "type"
        ].container
        expect(constant_value in schema_types).to_be_truthy()
        strings = load_json("homeassistant/components/sensor/strings.json")
        expect(
            constant_value in strings["device_automation"]["condition_type"]
        ).to_be_truthy()


@test
async def get_conditions(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_sensor_entities: dict[str, MockSensor] = Depends(mock_sensor_entities),
) -> None:
    """Test we get the expected conditions from a sensor."""
    setup_test_component_platform(hass, DOMAIN, mock_sensor_entities.values())
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()
    sensor_entries: dict[SensorDeviceClass, er.RegistryEntry] = {}

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    for device_class in SensorDeviceClass:
        sensor_entries[device_class] = entity_registry.async_get_or_create(
            DOMAIN,
            "test",
            mock_sensor_entities[device_class].unique_id,
            device_id=device_entry.id,
        )

    device_classes_without_condition = {
        SensorDeviceClass.DATE,
        SensorDeviceClass.ENUM,
        SensorDeviceClass.TIMESTAMP,
        SensorDeviceClass.UPTIME,
    }
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": condition["type"],
            "device_id": device_entry.id,
            "entity_id": sensor_entries[device_class].id,
            "metadata": {"secondary": False},
        }
        for device_class in SensorDeviceClass
        if device_class in UNITS_OF_MEASUREMENT
        and device_class not in device_classes_without_condition
        for condition in ENTITY_CONDITIONS[device_class]
        if device_class != "none"
    ]
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(len(conditions)).to_equal(57)
    expect(conditions).to_equal(unordered(expected_conditions))


@test.cases(
    test.case(
        "integration", hidden_by=RegistryEntryHider.INTEGRATION, entity_category=None
    ),
    test.case("user", hidden_by=RegistryEntryHider.USER, entity_category=None),
    test.case("config", hidden_by=None, entity_category=EntityCategory.CONFIG),
    test.case("diagnostic", hidden_by=None, entity_category=EntityCategory.DIAGNOSTIC),
)
async def get_conditions_hidden_auxiliary(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    hidden_by: RegistryEntryHider | None,
    entity_category: EntityCategory | None,
) -> None:
    """Test we get the expected conditions from a hidden or auxiliary entity."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        "5678",
        device_id=device_entry.id,
        entity_category=entity_category,
        hidden_by=hidden_by,
        unit_of_measurement="dogs",
    )
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": condition,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": True},
        }
        for condition in ("is_value",)
    ]
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(conditions).to_equal(unordered(expected_conditions))


@test
async def get_conditions_no_state(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected conditions from a sensor."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    sensor_entries: dict[SensorDeviceClass, er.RegistryEntry] = {}
    for device_class in SensorDeviceClass:
        sensor_entries[device_class] = entity_registry.async_get_or_create(
            DOMAIN,
            "test",
            f"5678_{device_class}",
            device_id=device_entry.id,
            original_device_class=device_class,
            unit_of_measurement=UNITS_OF_MEASUREMENT.get(device_class),
        )

    await hass.async_block_till_done()

    ignored_device_classes = {
        SensorDeviceClass.DATE,  # No condition
        SensorDeviceClass.ENUM,  # No condition
        SensorDeviceClass.TIMESTAMP,  # No condition
        SensorDeviceClass.UPTIME,  # No condition
        SensorDeviceClass.AQI,  # No unit of measurement
        SensorDeviceClass.PH,  # No unit of measurement
        SensorDeviceClass.MONETARY,  # No unit of measurement
    }
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": condition["type"],
            "device_id": device_entry.id,
            "entity_id": sensor_entries[device_class].id,
            "metadata": {"secondary": False},
        }
        for device_class in SensorDeviceClass
        if device_class in UNITS_OF_MEASUREMENT
        and device_class not in ignored_device_classes
        for condition in ENTITY_CONDITIONS[device_class]
    ]
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(conditions).to_equal(unordered(expected_conditions))


@test.cases(
    test.case(
        "measurement_no_unit",
        state_class=SensorStateClass.MEASUREMENT,
        unit=None,
        condition_types=["is_value"],
    ),
    test.case(
        "total_no_unit",
        state_class=SensorStateClass.TOTAL,
        unit=None,
        condition_types=["is_value"],
    ),
    test.case(
        "total_increasing_no_unit",
        state_class=SensorStateClass.TOTAL_INCREASING,
        unit=None,
        condition_types=["is_value"],
    ),
    test.case(
        "measurement_dogs",
        state_class=SensorStateClass.MEASUREMENT,
        unit="dogs",
        condition_types=["is_value"],
    ),
    test.case(
        "no_state_class_no_unit",
        state_class=None,
        unit=None,
        condition_types=[],
    ),
)
async def get_conditions_no_unit_or_stateclass(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    state_class: SensorStateClass | None,
    unit: str | None,
    condition_types: list[str],
) -> None:
    """Test we get the expected conditions from an entity with no unit or state class."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        "5678",
        capabilities={ATTR_STATE_CLASS: state_class},
        device_id=device_entry.id,
        unit_of_measurement=unit,
    )
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": condition,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
        for condition in condition_types
    ]
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(conditions).to_equal(unordered(expected_conditions))


@test.cases(
    test.case(
        "reg",
        set_state=False,
        device_class_reg=SensorDeviceClass.BATTERY,
        device_class_state=None,
        unit_reg=PERCENTAGE,
        unit_state=None,
    ),
    test.case(
        "state",
        set_state=True,
        device_class_reg=None,
        device_class_state=SensorDeviceClass.BATTERY,
        unit_reg=None,
        unit_state=PERCENTAGE,
    ),
)
async def get_condition_capabilities(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_sensor_entities: dict[str, MockSensor] = Depends(mock_sensor_entities),
    *,
    set_state: bool,
    device_class_reg: SensorDeviceClass | None,
    device_class_state: SensorDeviceClass | None,
    unit_reg: str | None,
    unit_state: str | None,
) -> None:
    """Test we get the expected capabilities from a sensor condition."""
    setup_test_component_platform(hass, DOMAIN, mock_sensor_entities.values())

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_id = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_sensor_entities["battery"].unique_id,
        device_id=device_entry.id,
        original_device_class=device_class_reg,
        unit_of_measurement=unit_reg,
    ).entity_id
    if set_state:
        hass.states.async_set(
            entity_id,
            None,
            {"device_class": device_class_state, "unit_of_measurement": unit_state},
        )

    expected_capabilities = {
        "extra_fields": [
            {
                "description": {"suffix": PERCENTAGE},
                "name": "above",
                "optional": True,
                "required": False,
                "type": "float",
            },
            {
                "description": {"suffix": PERCENTAGE},
                "name": "below",
                "optional": True,
                "required": False,
                "type": "float",
            },
        ]
    }
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(len(conditions)).to_equal(1)
    for condition in conditions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.CONDITION, condition
        )
        expect(capabilities).to_equal(expected_capabilities)


@test.cases(
    test.case(
        "reg",
        set_state=False,
        device_class_reg=SensorDeviceClass.BATTERY,
        device_class_state=None,
        unit_reg=PERCENTAGE,
        unit_state=None,
    ),
    test.case(
        "state",
        set_state=True,
        device_class_reg=None,
        device_class_state=SensorDeviceClass.BATTERY,
        unit_reg=None,
        unit_state=PERCENTAGE,
    ),
)
async def get_condition_capabilities_legacy(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_sensor_entities: dict[str, MockSensor] = Depends(mock_sensor_entities),
    *,
    set_state: bool,
    device_class_reg: SensorDeviceClass | None,
    device_class_state: SensorDeviceClass | None,
    unit_reg: str | None,
    unit_state: str | None,
) -> None:
    """Test we get the expected capabilities from a sensor condition."""
    setup_test_component_platform(hass, DOMAIN, mock_sensor_entities.values())

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_id = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_sensor_entities["battery"].unique_id,
        device_id=device_entry.id,
        original_device_class=device_class_reg,
        unit_of_measurement=unit_reg,
    ).entity_id
    if set_state:
        hass.states.async_set(
            entity_id,
            None,
            {"device_class": device_class_state, "unit_of_measurement": unit_state},
        )

    expected_capabilities = {
        "extra_fields": [
            {
                "description": {"suffix": PERCENTAGE},
                "name": "above",
                "optional": True,
                "required": False,
                "type": "float",
            },
            {
                "description": {"suffix": PERCENTAGE},
                "name": "below",
                "optional": True,
                "required": False,
                "type": "float",
            },
        ]
    }
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(len(conditions)).to_equal(1)
    for condition in conditions:
        condition["entity_id"] = entity_registry.async_get(
            condition["entity_id"]
        ).entity_id
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.CONDITION, condition
        )
        expect(capabilities).to_equal(expected_capabilities)


@test
async def get_condition_capabilities_none(
    hass: HomeAssistant = Depends(_condition_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a sensor condition."""
    entity = MockSensor(
        name="none sensor",
        unique_id="unique_none",
    )
    setup_test_component_platform(hass, DOMAIN, [entity])

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)

    entry_none = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        entity.unique_id,
    )

    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    conditions = [
        {
            "condition": "device",
            "device_id": "8770c43885354d5fa27604db6817f63f",
            "domain": "sensor",
            "entity_id": "01234567890123456789012345678901",
            "type": "is_battery_level",
        },
        {
            "condition": "device",
            "device_id": "8770c43885354d5fa27604db6817f63f",
            "domain": "sensor",
            "entity_id": entry_none.id,
            "type": "is_battery_level",
        },
    ]

    expected_capabilities = {}
    for condition in conditions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.CONDITION, condition
        )
        expect(capabilities).to_equal(expected_capabilities)


@test
async def if_state_not_above_below(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for bad value conditions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": {"platform": "event", "event_type": "test_event1"},
                        "condition": [
                            {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "is_battery_level",
                            }
                        ],
                        "action": {"service": "test.automation"},
                    }
                ]
            },
        )
    ).to_be_truthy()
    expect("must contain at least one of below, above" in caplog.text).to_be_truthy()


@test
async def if_state_above(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for value conditions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, STATE_UNKNOWN, {"device_class": "battery"})

    service_calls = async_mock_service(hass, "test", "automation")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": {"platform": "event", "event_type": "test_event1"},
                        "condition": [
                            {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "is_battery_level",
                                "above": 10,
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "{{ trigger.platform }}"
                                    " - {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, 9)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, 11)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("event - test_event1")


@test
async def if_state_above_legacy(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for value conditions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, STATE_UNKNOWN, {"device_class": "battery"})

    service_calls = async_mock_service(hass, "test", "automation")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": {"platform": "event", "event_type": "test_event1"},
                        "condition": [
                            {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.entity_id,
                                "type": "is_battery_level",
                                "above": 10,
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "{{ trigger.platform }}"
                                    " - {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, 9)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, 11)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("event - test_event1")


@test
async def if_state_below(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for value conditions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, STATE_UNKNOWN, {"device_class": "battery"})

    service_calls = async_mock_service(hass, "test", "automation")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": {"platform": "event", "event_type": "test_event1"},
                        "condition": [
                            {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "is_battery_level",
                                "below": 10,
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "{{ trigger.platform }}"
                                    " - {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, 11)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, 9)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("event - test_event1")


@test
async def if_state_between(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for value conditions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, STATE_UNKNOWN, {"device_class": "battery"})

    service_calls = async_mock_service(hass, "test", "automation")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": {"platform": "event", "event_type": "test_event1"},
                        "condition": [
                            {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "is_battery_level",
                                "above": 10,
                                "below": 20,
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "{{ trigger.platform }}"
                                    " - {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    }
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, 9)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, 11)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("event - test_event1")

    hass.states.async_set(entry.entity_id, 21)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set(entry.entity_id, 19)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal("event - test_event1")
