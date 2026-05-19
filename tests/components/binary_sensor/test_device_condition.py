"""The test for binary_sensor device automation (tryke port)."""

from datetime import timedelta

from freezegun import freeze_time
from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.binary_sensor import DOMAIN, BinarySensorDeviceClass
from homeassistant.components.binary_sensor.device_condition import ENTITY_CONDITIONS
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.const import CONF_PLATFORM, STATE_OFF, STATE_ON, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryHider
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from .common import MockBinarySensor

from tests.common import (
    MockConfigEntry,
    async_get_device_automation_capabilities,
    async_get_device_automations,
    async_mock_service,
    setup_test_component_platform,
)
from tests.hass_fixtures import (
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
def mock_binary_sensor_entities() -> dict[str, MockBinarySensor]:
    """Return mock binary sensors."""
    return {
        device_class: MockBinarySensor(
            name=f"{device_class} sensor",
            is_on=True,
            unique_id=f"unique_{device_class}",
            device_class=device_class,
        )
        for device_class in BinarySensorDeviceClass
    }


@test
async def get_conditions(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_binary_sensor_entities: dict[str, MockBinarySensor] = Depends(
        mock_binary_sensor_entities
    ),
) -> None:
    """Test we get the expected conditions from a binary_sensor."""
    setup_test_component_platform(hass, DOMAIN, mock_binary_sensor_entities.values())
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()
    binary_sensor_entries: dict[BinarySensorDeviceClass, er.RegistryEntry] = {}

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    for device_class in BinarySensorDeviceClass:
        binary_sensor_entries[device_class] = entity_registry.async_get_or_create(
            DOMAIN,
            "test",
            mock_binary_sensor_entities[device_class].unique_id,
            device_id=device_entry.id,
        )

    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": condition["type"],
            "device_id": device_entry.id,
            "entity_id": binary_sensor_entries[device_class].id,
            "metadata": {"secondary": False},
        }
        for device_class in BinarySensorDeviceClass
        for condition in ENTITY_CONDITIONS[device_class]
    ]
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
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
        for condition in ("is_on", "is_off")
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
    """Test we get the expected conditions from a binary_sensor."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    binary_sensor_entries: dict[BinarySensorDeviceClass, er.RegistryEntry] = {}
    for device_class in BinarySensorDeviceClass:
        binary_sensor_entries[device_class] = entity_registry.async_get_or_create(
            DOMAIN,
            "test",
            f"5678_{device_class}",
            device_id=device_entry.id,
            original_device_class=device_class,
        )

    await hass.async_block_till_done()

    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": condition["type"],
            "device_id": device_entry.id,
            "entity_id": binary_sensor_entries[device_class].id,
            "metadata": {"secondary": False},
        }
        for device_class in BinarySensorDeviceClass
        for condition in ENTITY_CONDITIONS[device_class]
    ]
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(conditions).to_equal(expected_conditions)


@test
async def get_condition_capabilities(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a binary_sensor condition."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )
    expected_capabilities = {
        "extra_fields": [
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ]
    }
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    for condition in conditions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.CONDITION, condition
        )
        expect(capabilities).to_equal(expected_capabilities)


@test
async def get_condition_capabilities_legacy(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a binary_sensor condition."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )
    expected_capabilities = {
        "extra_fields": [
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ]
    }
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    for condition in conditions:
        condition["entity_id"] = entity_registry.async_get(
            condition["entity_id"]
        ).entity_id
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.CONDITION, condition
        )
        expect(capabilities).to_equal(expected_capabilities)


@test
async def if_state(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_binary_sensor_entities: dict[str, MockBinarySensor] = Depends(
        mock_binary_sensor_entities
    ),
) -> None:
    """Test for turn_on and turn_off conditions."""
    setup_test_component_platform(hass, DOMAIN, mock_binary_sensor_entities.values())
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get(mock_binary_sensor_entities["battery"].entity_id)
    entity_registry.async_update_entity(entry.entity_id, device_id=device_entry.id)

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
                                "type": "is_bat_low",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_on {{ trigger.platform }}"
                                    " - {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                    {
                        "trigger": {"platform": "event", "event_type": "test_event2"},
                        "condition": [
                            {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "is_not_bat_low",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_off {{ trigger.platform }}"
                                    " - {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(hass.states.get(entry.entity_id).state).to_equal(STATE_ON)
    expect(len(service_calls)).to_equal(0)

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("is_on event - test_event1")

    hass.states.async_set(entry.entity_id, STATE_OFF)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal("is_off event - test_event2")


@test
async def if_state_legacy(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_binary_sensor_entities: dict[str, MockBinarySensor] = Depends(
        mock_binary_sensor_entities
    ),
) -> None:
    """Test for turn_on and turn_off conditions."""
    setup_test_component_platform(hass, DOMAIN, mock_binary_sensor_entities.values())
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get(mock_binary_sensor_entities["battery"].entity_id)
    entity_registry.async_update_entity(entry.entity_id, device_id=device_entry.id)

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
                                "type": "is_bat_low",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_on {{ trigger.platform }}"
                                    " - {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(hass.states.get(entry.entity_id).state).to_equal(STATE_ON)
    expect(len(service_calls)).to_equal(0)

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("is_on event - test_event1")


@test
async def if_fires_on_for_condition(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_binary_sensor_entities: dict[str, MockBinarySensor] = Depends(
        mock_binary_sensor_entities
    ),
) -> None:
    """Test for firing if condition is on with delay."""
    point1 = dt_util.utcnow()
    point2 = point1 + timedelta(seconds=10)
    point3 = point2 + timedelta(seconds=10)

    setup_test_component_platform(hass, DOMAIN, mock_binary_sensor_entities.values())
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get(mock_binary_sensor_entities["battery"].entity_id)
    entity_registry.async_update_entity(entry.entity_id, device_id=device_entry.id)

    service_calls = async_mock_service(hass, "test", "automation")

    with freeze_time(point1) as time_freeze:
        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: [
                        {
                            "trigger": {
                                "platform": "event",
                                "event_type": "test_event1",
                            },
                            "condition": {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "is_not_bat_low",
                                "for": {"seconds": 5},
                            },
                            "action": {
                                "service": "test.automation",
                                "data_template": {
                                    "some": (
                                        "is_off {{ trigger.platform }}"
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
        expect(hass.states.get(entry.entity_id).state).to_equal(STATE_ON)
        expect(len(service_calls)).to_equal(0)

        hass.bus.async_fire("test_event1")
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(0)

        # Time travel 10 secs into the future
        time_freeze.move_to(point2)
        hass.bus.async_fire("test_event1")
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(0)

        hass.states.async_set(entry.entity_id, STATE_OFF)
        hass.bus.async_fire("test_event1")
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(0)

        # Time travel 20 secs into the future
        time_freeze.move_to(point3)
        hass.bus.async_fire("test_event1")
        await hass.async_block_till_done()
        expect(len(service_calls)).to_equal(1)
        expect(service_calls[0].data["some"]).to_equal("is_off event - test_event1")
