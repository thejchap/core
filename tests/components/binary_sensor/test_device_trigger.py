"""The test for binary_sensor device automation (tryke port)."""

from datetime import timedelta

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.binary_sensor import DOMAIN, BinarySensorDeviceClass
from homeassistant.components.binary_sensor.device_trigger import ENTITY_TRIGGERS
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
    async_fire_time_changed,
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
def _trigger_executor(
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
async def get_triggers(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_binary_sensor_entities: dict[str, MockBinarySensor] = Depends(
        mock_binary_sensor_entities
    ),
) -> None:
    """Test we get the expected triggers from a binary_sensor."""
    registry_entries: dict[BinarySensorDeviceClass, er.RegistryEntry] = {}
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
    for device_class in BinarySensorDeviceClass:
        registry_entries[device_class] = entity_registry.async_get_or_create(
            DOMAIN,
            "test",
            mock_binary_sensor_entities[device_class].unique_id,
            device_id=device_entry.id,
        )

    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": trigger["type"],
            "device_id": device_entry.id,
            "entity_id": registry_entries[device_class].id,
            "metadata": {"secondary": False},
        }
        for device_class in BinarySensorDeviceClass
        for trigger in ENTITY_TRIGGERS[device_class]
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
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
    entry = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        "5678",
        device_id=device_entry.id,
        entity_category=entity_category,
        hidden_by=hidden_by,
    )
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": trigger,
            "device_id": device_entry.id,
            "entity_id": entry.id,
            "metadata": {"secondary": True},
        }
        for trigger in ("turned_on", "turned_off")
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(triggers).to_equal(unordered(expected_triggers))


@test
async def get_triggers_no_state(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_binary_sensor_entities: dict[str, MockBinarySensor] = Depends(
        mock_binary_sensor_entities
    ),
) -> None:
    """Test we get the expected triggers from a binary_sensor."""
    registry_entries: dict[BinarySensorDeviceClass, er.RegistryEntry] = {}
    setup_test_component_platform(hass, DOMAIN, mock_binary_sensor_entities.values())

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    for device_class in BinarySensorDeviceClass:
        registry_entries[device_class] = entity_registry.async_get_or_create(
            DOMAIN,
            "test",
            f"5678_{device_class}",
            device_id=device_entry.id,
            original_device_class=device_class,
        )

    await hass.async_block_till_done()

    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": trigger["type"],
            "device_id": device_entry.id,
            "entity_id": registry_entries[device_class].id,
            "metadata": {"secondary": False},
        }
        for device_class in BinarySensorDeviceClass
        for trigger in ENTITY_TRIGGERS[device_class]
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(triggers).to_equal(unordered(expected_triggers))


@test
async def get_trigger_capabilities(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a binary_sensor trigger."""
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
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    for trigger in triggers:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.TRIGGER, trigger
        )
        expect(capabilities).to_equal(expected_capabilities)


@test
async def get_trigger_capabilities_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a binary_sensor trigger."""
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
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    for trigger in triggers:
        trigger["entity_id"] = entity_registry.async_get(trigger["entity_id"]).entity_id
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.TRIGGER, trigger
        )
        expect(capabilities).to_equal(expected_capabilities)


@test
async def if_fires_on_state_change(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_binary_sensor_entities: dict[str, MockBinarySensor] = Depends(
        mock_binary_sensor_entities
    ),
) -> None:
    """Test for on and off triggers firing."""
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
    entry = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_binary_sensor_entities["battery"].unique_id,
        device_id=device_entry.id,
    )

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
                            "type": "bat_low",
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
                    },
                    {
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "not_bat_low",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "not_bat_low {{ trigger.platform }}"
                                    " - {{ trigger.entity_id }}"
                                    " - {{ trigger.from_state.state }}"
                                    " - {{ trigger.to_state.state }}"
                                    " - {{ trigger.for }}"
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

    hass.states.async_set(entry.entity_id, STATE_OFF)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"not_bat_low device - {entry.entity_id} - on - off - None"
    )

    hass.states.async_set(entry.entity_id, STATE_ON)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal(
        f"bat_low device - {entry.entity_id} - off - on - None"
    )


@test
async def if_fires_on_state_change_with_for(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_binary_sensor_entities: dict[str, MockBinarySensor] = Depends(
        mock_binary_sensor_entities
    ),
) -> None:
    """Test for triggers firing with delay."""
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
    entry = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_binary_sensor_entities["battery"].unique_id,
        device_id=device_entry.id,
    )

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
                            "type": "turned_off",
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
    expect(hass.states.get(entry.entity_id).state).to_equal(STATE_ON)
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, STATE_OFF)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    await hass.async_block_till_done()
    expect(service_calls[0].data["some"]).to_equal(
        f"turn_off device - {entry.entity_id} - on - off - 0:00:05"
    )


@test
async def if_fires_on_state_change_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_binary_sensor_entities: dict[str, MockBinarySensor] = Depends(
        mock_binary_sensor_entities
    ),
) -> None:
    """Test for triggers firing."""
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
    entry = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_binary_sensor_entities["battery"].unique_id,
        device_id=device_entry.id,
    )

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
                            "type": "turned_off",
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
    expect(hass.states.get(entry.entity_id).state).to_equal(STATE_ON)
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, STATE_OFF)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"turn_off device - {entry.entity_id} - on - off - None"
    )
