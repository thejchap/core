"""The tests for Select device conditions (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test
import voluptuous_serialize

from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.select import DOMAIN
from homeassistant.components.select.device_condition import (
    async_get_condition_capabilities,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.entity_registry import RegistryEntryHider
from homeassistant.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    async_get_device_automations,
    async_mock_service,
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


@test
async def get_conditions(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected conditions from a select."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": "selected_option",
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
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
        for condition in ("selected_option",)
    ]
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(conditions).to_equal(unordered(expected_conditions))


@test
async def if_selected_option(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for selected_option conditions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

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
                                "type": "selected_option",
                                "option": "option1",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data": {
                                "result": "option1 - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                                "type": "selected_option",
                                "option": "option2",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data": {
                                "result": "option2 - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(
        entry.entity_id, "option1", {"options": ["option1", "option2"]}
    )
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["result"]).to_equal("option1 - event - test_event1")

    hass.states.async_set(
        entry.entity_id, "option2", {"options": ["option1", "option2"]}
    )
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["result"]).to_equal("option2 - event - test_event2")


@test
async def if_selected_option_legacy(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for selected_option conditions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

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
                                "type": "selected_option",
                                "option": "option1",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data": {
                                "result": "option1 - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    hass.states.async_set(
        entry.entity_id, "option1", {"options": ["option1", "option2"]}
    )
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["result"]).to_equal("option1 - event - test_event1")


@test
async def get_condition_capabilities(
    hass: HomeAssistant = Depends(_condition_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a select condition."""
    entry = entity_registry.async_get_or_create(DOMAIN, "test", "5678")

    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "selected_option",
        "entity_id": entry.id,
        "option": "option1",
    }

    capabilities = await async_get_condition_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "option",
                "required": True,
                "type": "select",
                "options": [],
            },
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            },
        ]
    )

    hass.states.async_set(
        entry.entity_id, "option1", {"options": ["option1", "option2"]}
    )

    capabilities = await async_get_condition_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "option",
                "required": True,
                "type": "select",
                "options": [("option1", "option1"), ("option2", "option2")],
            },
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            },
        ]
    )


@test
async def get_condition_capabilities_legacy(
    hass: HomeAssistant = Depends(_condition_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a select condition."""
    entry = entity_registry.async_get_or_create(DOMAIN, "test", "5678")

    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "selected_option",
        "entity_id": entry.entity_id,
        "option": "option1",
    }

    capabilities = await async_get_condition_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "option",
                "required": True,
                "type": "select",
                "options": [],
            },
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            },
        ]
    )

    hass.states.async_set(
        entry.entity_id, "option1", {"options": ["option1", "option2"]}
    )

    capabilities = await async_get_condition_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "option",
                "required": True,
                "type": "select",
                "options": [("option1", "option1"), ("option2", "option2")],
            },
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            },
        ]
    )
