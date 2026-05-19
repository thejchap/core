"""The tests for Select device triggers (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test
import voluptuous_serialize

from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.select import DOMAIN
from homeassistant.components.select.device_trigger import (
    async_get_trigger_capabilities,
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
def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture for the module."""
    return hass


@test
async def get_triggers(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected triggers from a select."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": "current_option_changed",
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
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
    entity_entry = entity_registry.async_get_or_create(
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
            "entity_id": entity_entry.id,
            "metadata": {"secondary": True},
        }
        for trigger in ("current_option_changed",)
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(triggers).to_equal(unordered(expected_triggers))


@test
async def if_fires_on_state_change(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for turn_on and turn_off triggers firing."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(
        entry.entity_id, "option1", {"options": ["option1", "option2", "option3"]}
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
                            "type": "current_option_changed",
                            "to": "option2",
                        },
                        "action": {
                            "service": "test.automation",
                            "data": {
                                "some": (
                                    "to - {{ trigger.platform}} - "
                                    "{{ trigger.entity_id}} - {{ trigger.from_state.state}} - "
                                    "{{ trigger.to_state.state}} - {{ trigger.for }} - "
                                    "{{ trigger.id}}"
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
                            "type": "current_option_changed",
                            "from": "option2",
                        },
                        "action": {
                            "service": "test.automation",
                            "data": {
                                "some": (
                                    "from - {{ trigger.platform}} - "
                                    "{{ trigger.entity_id}} - {{ trigger.from_state.state}} - "
                                    "{{ trigger.to_state.state}} - {{ trigger.for }} - "
                                    "{{ trigger.id}}"
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
                            "type": "current_option_changed",
                            "from": "option3",
                            "to": "option1",
                        },
                        "action": {
                            "service": "test.automation",
                            "data": {
                                "some": (
                                    "from-to - {{ trigger.platform}} - "
                                    "{{ trigger.entity_id}} - {{ trigger.from_state.state}} - "
                                    "{{ trigger.to_state.state}} - {{ trigger.for }} - "
                                    "{{ trigger.id}}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    hass.states.async_set(entry.entity_id, "option2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"to - device - {entry.entity_id} - option1 - option2 - None - 0"
    )

    hass.states.async_set(entry.entity_id, "option3")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal(
        f"from - device - {entry.entity_id} - option2 - option3 - None - 0"
    )

    hass.states.async_set(entry.entity_id, "option1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect(service_calls[2].data["some"]).to_equal(
        f"from-to - device - {entry.entity_id} - option3 - option1 - None - 0"
    )


@test
async def if_fires_on_state_change_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for turn_on and turn_off triggers firing."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(
        entry.entity_id, "option1", {"options": ["option1", "option2", "option3"]}
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
                            "type": "current_option_changed",
                            "to": "option2",
                        },
                        "action": {
                            "service": "test.automation",
                            "data": {
                                "some": (
                                    "to - {{ trigger.platform}} - "
                                    "{{ trigger.entity_id}} - {{ trigger.from_state.state}} - "
                                    "{{ trigger.to_state.state}} - {{ trigger.for }} - "
                                    "{{ trigger.id}}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    hass.states.async_set(entry.entity_id, "option2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"to - device - {entry.entity_id} - option1 - option2 - None - 0"
    )


@test
async def get_trigger_capabilities(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a select trigger."""
    entry = entity_registry.async_get_or_create(DOMAIN, "test", "5678")

    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "current_option_changed",
        "entity_id": entry.id,
        "to": "option1",
    }

    capabilities = await async_get_trigger_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "from",
                "optional": True,
                "required": False,
                "type": "select",
                "options": [],
            },
            {
                "name": "to",
                "optional": True,
                "required": False,
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

    capabilities = await async_get_trigger_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "from",
                "optional": True,
                "required": False,
                "type": "select",
                "options": [("option1", "option1"), ("option2", "option2")],
            },
            {
                "name": "to",
                "optional": True,
                "required": False,
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
async def get_trigger_capabilities_unknown(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a select trigger."""
    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "current_option_changed",
        "entity_id": "12345",
        "to": "option1",
    }

    capabilities = await async_get_trigger_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "from",
                "optional": True,
                "required": False,
                "type": "select",
                "options": [],
            },
            {
                "name": "to",
                "optional": True,
                "required": False,
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


@test
async def get_trigger_capabilities_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a select trigger."""
    entry = entity_registry.async_get_or_create(DOMAIN, "test", "5678")

    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "current_option_changed",
        "entity_id": entry.entity_id,
        "to": "option1",
    }

    capabilities = await async_get_trigger_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "from",
                "optional": True,
                "required": False,
                "type": "select",
                "options": [],
            },
            {
                "name": "to",
                "optional": True,
                "required": False,
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

    capabilities = await async_get_trigger_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "from",
                "optional": True,
                "required": False,
                "type": "select",
                "options": [("option1", "option1"), ("option2", "option2")],
            },
            {
                "name": "to",
                "optional": True,
                "required": False,
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
