"""The test for sensor device automation (tryke port)."""

from collections.abc import Generator
from datetime import timedelta

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
    device_trigger,
)
from homeassistant.components.sensor.const import NON_NUMERIC_DEVICE_CLASSES
from homeassistant.components.sensor.device_trigger import ENTITY_TRIGGERS
from homeassistant.const import CONF_PLATFORM, PERCENTAGE, STATE_UNKNOWN, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryHider
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from homeassistant.util.json import load_json

from .common import UNITS_OF_MEASUREMENT, MockSensor, get_mock_sensor_entities

from tests.common import (
    MockConfigEntry,
    async_fire_time_changed,
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
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture for the module."""
    return hass


@fixture
def enable_custom_integrations(
    hass: HomeAssistant = Depends(_trigger_executor),
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
    """Ensure device class constants are declared in device_trigger module."""
    for device_class in SensorDeviceClass:
        if device_class in NON_NUMERIC_DEVICE_CLASSES:
            continue
        constant_name = {
            SensorDeviceClass.BATTERY: "CONF_BATTERY_LEVEL",
            SensorDeviceClass.CO: "CONF_CO",
            SensorDeviceClass.CO2: "CONF_CO2",
            SensorDeviceClass.ENERGY_STORAGE: "CONF_ENERGY",
            SensorDeviceClass.VOLUME_STORAGE: "CONF_VOLUME",
        }.get(device_class, f"CONF_{device_class.value.upper()}")
        expect(hasattr(device_trigger, constant_name)).to_be_truthy()

        constant_value = {
            SensorDeviceClass.BATTERY: "battery_level",
            SensorDeviceClass.ENERGY_STORAGE: "energy",
            SensorDeviceClass.VOLUME_STORAGE: "volume",
        }.get(device_class, device_class.value)
        expect(getattr(device_trigger, constant_name)).to_equal(constant_value)

        expect(device_class in ENTITY_TRIGGERS).to_be_truthy()
        schema_types = device_trigger.TRIGGER_SCHEMA.validators[0].schema[
            "type"
        ].container
        expect(constant_value in schema_types).to_be_truthy()
        strings = load_json("homeassistant/components/sensor/strings.json")
        expect(
            constant_value in strings["device_automation"]["trigger_type"]
        ).to_be_truthy()


@test
async def get_triggers(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_sensor_entities: dict[str, MockSensor] = Depends(mock_sensor_entities),
) -> None:
    """Test we get the expected triggers from a sensor."""
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

    device_classes_without_trigger = {
        SensorDeviceClass.DATE,
        SensorDeviceClass.ENUM,
        SensorDeviceClass.TIMESTAMP,
        SensorDeviceClass.UPTIME,
    }
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": trigger["type"],
            "device_id": device_entry.id,
            "entity_id": sensor_entries[device_class].id,
            "metadata": {"secondary": False},
        }
        for device_class in SensorDeviceClass
        if device_class in UNITS_OF_MEASUREMENT
        and device_class not in device_classes_without_trigger
        for trigger in ENTITY_TRIGGERS[device_class]
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(len(triggers)).to_equal(57)
    expect(triggers).to_equal(unordered(expected_triggers))


@test.cases(
    test.case(
        "integration", hidden_by=RegistryEntryHider.INTEGRATION, entity_category=None
    ),
    test.case("user", hidden_by=RegistryEntryHider.USER, entity_category=None),
    test.case("config", hidden_by=None, entity_category=EntityCategory.CONFIG),
    test.case("diagnostic", hidden_by=None, entity_category=EntityCategory.DIAGNOSTIC),
)
async def get_triggers_hidden_auxiliary(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    hidden_by: RegistryEntryHider | None,
    entity_category: EntityCategory | None,
) -> None:
    """Test we get the expected triggers from a hidden or auxiliary entity."""
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
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": trigger,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": True},
        }
        for trigger in ("value",)
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(triggers).to_equal(unordered(expected_triggers))


@test.cases(
    test.case(
        "measurement_no_unit",
        state_class=SensorStateClass.MEASUREMENT,
        unit=None,
        trigger_types=["value"],
    ),
    test.case(
        "total_no_unit",
        state_class=SensorStateClass.TOTAL,
        unit=None,
        trigger_types=["value"],
    ),
    test.case(
        "total_increasing_no_unit",
        state_class=SensorStateClass.TOTAL_INCREASING,
        unit=None,
        trigger_types=["value"],
    ),
    test.case(
        "measurement_dogs",
        state_class=SensorStateClass.MEASUREMENT,
        unit="dogs",
        trigger_types=["value"],
    ),
    test.case(
        "no_state_class_no_unit",
        state_class=None,
        unit=None,
        trigger_types=[],
    ),
)
async def get_triggers_no_unit_or_stateclass(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    state_class: SensorStateClass | None,
    unit: str | None,
    trigger_types: list[str],
) -> None:
    """Test we get the expected triggers from an entity with no unit or state class."""
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
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": trigger,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
        for trigger in trigger_types
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(triggers).to_equal(unordered(expected_triggers))


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
async def get_trigger_capabilities(
    hass: HomeAssistant = Depends(_trigger_executor),
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
    """Test we get the expected capabilities from a sensor trigger."""
    setup_test_component_platform(hass, DOMAIN, mock_sensor_entities)

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
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            },
        ]
    }
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(len(triggers)).to_equal(1)
    for trigger in triggers:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.TRIGGER, trigger
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
async def get_trigger_capabilities_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
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
    """Test we get the expected capabilities from a sensor trigger."""
    setup_test_component_platform(hass, DOMAIN, mock_sensor_entities)

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
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            },
        ]
    }
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(len(triggers)).to_equal(1)
    for trigger in triggers:
        trigger["entity_id"] = entity_registry.async_get(trigger["entity_id"]).entity_id
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.TRIGGER, trigger
        )
        expect(capabilities).to_equal(expected_capabilities)


@test
async def get_trigger_capabilities_none(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a sensor trigger."""
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

    triggers = [
        {
            "platform": "device",
            "device_id": "8770c43885354d5fa27604db6817f63f",
            "domain": "sensor",
            "entity_id": "01234567890123456789012345678901",
            "type": "is_battery_level",
        },
        {
            "platform": "device",
            "device_id": "8770c43885354d5fa27604db6817f63f",
            "domain": "sensor",
            "entity_id": entry_none.id,
            "type": "is_battery_level",
        },
    ]

    expected_capabilities = {}
    for trigger in triggers:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.TRIGGER, trigger
        )
        expect(capabilities).to_equal(expected_capabilities)


@test
async def if_fires_not_on_above_below(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for value triggers firing."""
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
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "battery_level",
                        },
                        "action": {"service": "test.automation"},
                    }
                ]
            },
        )
    ).to_be_truthy()
    expect("must contain at least one of below, above" in caplog.text).to_be_truthy()


@test
async def if_fires_on_state_above(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for value triggers firing."""
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
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "battery_level",
                            "above": 10,
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "bat_low {{ trigger.platform }}"
                                    " - {{ trigger.entity_id }}"
                                    " - {{ trigger.from_state.state }}"
                                    " - {{ trigger.to_state.state }}"
                                    " - {{ trigger.for }}"
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

    hass.states.async_set(entry.entity_id, 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, 11)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"bat_low device - {entry.entity_id} - 9 - 11 - None"
    )


@test
async def if_fires_on_state_below(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for value triggers firing."""
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
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "battery_level",
                            "below": 10,
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "bat_low {{ trigger.platform }}"
                                    " - {{ trigger.entity_id }}"
                                    " - {{ trigger.from_state.state }}"
                                    " - {{ trigger.to_state.state }}"
                                    " - {{ trigger.for }}"
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

    hass.states.async_set(entry.entity_id, 11)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"bat_low device - {entry.entity_id} - 11 - 9 - None"
    )


@test
async def if_fires_on_state_between(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for value triggers firing."""
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
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "battery_level",
                            "above": 10,
                            "below": 20,
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "bat_low {{ trigger.platform }}"
                                    " - {{ trigger.entity_id }}"
                                    " - {{ trigger.from_state.state }}"
                                    " - {{ trigger.to_state.state }}"
                                    " - {{ trigger.for }}"
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

    hass.states.async_set(entry.entity_id, 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, 11)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"bat_low device - {entry.entity_id} - 9 - 11 - None"
    )

    hass.states.async_set(entry.entity_id, 21)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set(entry.entity_id, 19)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal(
        f"bat_low device - {entry.entity_id} - 21 - 19 - None"
    )


@test
async def if_fires_on_state_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for value triggers firing."""
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
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.entity_id,
                            "type": "battery_level",
                            "above": 10,
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "bat_low {{ trigger.platform }}"
                                    " - {{ trigger.entity_id }}"
                                    " - {{ trigger.from_state.state }}"
                                    " - {{ trigger.to_state.state }}"
                                    " - {{ trigger.for }}"
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

    hass.states.async_set(entry.entity_id, 9)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, 11)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"bat_low device - {entry.entity_id} - 9 - 11 - None"
    )


@test
async def if_fires_on_state_change_with_for(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for triggers firing with delay."""
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
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "battery_level",
                            "above": 10,
                            "for": {"seconds": 5},
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "turn_off {{ trigger.platform }}"
                                    " - {{ trigger.entity_id }}"
                                    " - {{ trigger.from_state.state }}"
                                    " - {{ trigger.to_state.state }}"
                                    " - {{ trigger.for }}"
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

    hass.states.async_set(entry.entity_id, 10)
    hass.states.async_set(entry.entity_id, 11)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    await hass.async_block_till_done()
    expect(service_calls[0].data["some"]).to_equal(
        f"turn_off device - {entry.entity_id} - 10 - 11 - 0:00:05"
    )
