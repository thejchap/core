"""The tests for Select device actions (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test
import voluptuous_serialize

from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.select import DOMAIN
from homeassistant.components.select.device_action import async_get_action_capabilities
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
async def get_actions(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected actions from a select."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": action,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
        for action in (
            "select_first",
            "select_last",
            "select_next",
            "select_option",
            "select_previous",
        )
    ]
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(actions).to_equal(unordered(expected_actions))


@test.cases(
    test.case("integration", hidden_by=RegistryEntryHider.INTEGRATION, entity_category=None),
    test.case("user", hidden_by=RegistryEntryHider.USER, entity_category=None),
    test.case("config", hidden_by=None, entity_category=EntityCategory.CONFIG),
    test.case("diagnostic", hidden_by=None, entity_category=EntityCategory.DIAGNOSTIC),
)
async def get_actions_hidden_auxiliary(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    hidden_by: RegistryEntryHider | None,
    entity_category: EntityCategory | None,
) -> None:
    """Test we get the expected actions from a hidden or auxiliary entity."""
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
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": action,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": True},
        }
        for action in (
            "select_first",
            "select_last",
            "select_next",
            "select_option",
            "select_previous",
        )
    ]
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(actions).to_equal(unordered(expected_actions))


@test.cases(
    test.case("select_first", action_type="select_first"),
    test.case("select_last", action_type="select_last"),
)
async def action_select_first_last(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    action_type: str,
) -> None:
    """Test for select_first and select_last actions."""
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
                            "platform": "event",
                            "event_type": "test_event",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": action_type,
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    select_calls = async_mock_service(hass, DOMAIN, action_type)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(select_calls)).to_equal(1)
    expect(select_calls[0].domain).to_equal(DOMAIN)
    expect(select_calls[0].service).to_equal(action_type)
    expect(select_calls[0].data).to_equal({"entity_id": entry.entity_id})


@test.cases(
    test.case("select_first", action_type="select_first"),
    test.case("select_last", action_type="select_last"),
)
async def action_select_first_last_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    action_type: str,
) -> None:
    """Test for select_first and select_last actions."""
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
                            "platform": "event",
                            "event_type": "test_event",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.entity_id,
                            "type": action_type,
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    select_calls = async_mock_service(hass, DOMAIN, action_type)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(select_calls)).to_equal(1)
    expect(select_calls[0].domain).to_equal(DOMAIN)
    expect(select_calls[0].service).to_equal(action_type)
    expect(select_calls[0].data).to_equal({"entity_id": entry.entity_id})


@test
async def action_select_option(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for select_option action."""
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
                            "platform": "event",
                            "event_type": "test_event",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "select_option",
                            "option": "option1",
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    select_calls = async_mock_service(hass, DOMAIN, "select_option")

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(select_calls)).to_equal(1)
    expect(select_calls[0].domain).to_equal(DOMAIN)
    expect(select_calls[0].service).to_equal("select_option")
    expect(select_calls[0].data).to_equal(
        {"entity_id": entry.entity_id, "option": "option1"}
    )


@test.cases(
    test.case("select_next", action_type="select_next"),
    test.case("select_previous", action_type="select_previous"),
)
async def action_select_next_previous(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    action_type: str,
) -> None:
    """Test for select_next and select_previous actions."""
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
                            "platform": "event",
                            "event_type": "test_event",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": action_type,
                            "cycle": False,
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    select_calls = async_mock_service(hass, DOMAIN, action_type)

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()
    expect(len(select_calls)).to_equal(1)
    expect(select_calls[0].domain).to_equal(DOMAIN)
    expect(select_calls[0].service).to_equal(action_type)
    expect(select_calls[0].data).to_equal(
        {"entity_id": entry.entity_id, "cycle": False}
    )


@test
async def get_action_capabilities(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a select action."""
    entry = entity_registry.async_get_or_create(DOMAIN, "test", "5678")

    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "select_option",
        "entity_id": entry.id,
        "option": "option1",
    }

    capabilities = await async_get_action_capabilities(hass, config)
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
        ]
    )

    hass.states.async_set(
        entry.entity_id, "option1", {"options": ["option1", "option2"]}
    )

    capabilities = await async_get_action_capabilities(hass, config)
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
        ]
    )

    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "select_next",
        "entity_id": entry.id,
    }
    capabilities = await async_get_action_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "cycle",
                "optional": True,
                "required": False,
                "type": "boolean",
                "default": True,
            },
        ]
    )

    config["type"] = "select_previous"
    capabilities = await async_get_action_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "cycle",
                "optional": True,
                "required": False,
                "type": "boolean",
                "default": True,
            },
        ]
    )

    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "select_first",
        "entity_id": entry.id,
    }
    capabilities = await async_get_action_capabilities(hass, config)
    expect(capabilities).to_equal({})

    config["type"] = "select_last"
    capabilities = await async_get_action_capabilities(hass, config)
    expect(capabilities).to_equal({})


@test
async def get_action_capabilities_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a select action."""
    entry = entity_registry.async_get_or_create(DOMAIN, "test", "5678")

    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "select_option",
        "entity_id": entry.entity_id,
        "option": "option1",
    }

    capabilities = await async_get_action_capabilities(hass, config)
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
        ]
    )

    hass.states.async_set(
        entry.entity_id, "option1", {"options": ["option1", "option2"]}
    )

    capabilities = await async_get_action_capabilities(hass, config)
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
        ]
    )

    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "select_next",
        "entity_id": entry.entity_id,
    }
    capabilities = await async_get_action_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "cycle",
                "optional": True,
                "required": False,
                "type": "boolean",
                "default": True,
            },
        ]
    )

    config["type"] = "select_previous"
    capabilities = await async_get_action_capabilities(hass, config)
    expect(capabilities).to_be_truthy()
    expect("extra_fields" in capabilities).to_be_truthy()
    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(
        [
            {
                "name": "cycle",
                "optional": True,
                "required": False,
                "type": "boolean",
                "default": True,
            },
        ]
    )

    config = {
        "platform": "device",
        "domain": DOMAIN,
        "type": "select_first",
        "entity_id": entry.entity_id,
    }
    capabilities = await async_get_action_capabilities(hass, config)
    expect(capabilities).to_equal({})

    config["type"] = "select_last"
    capabilities = await async_get_action_capabilities(hass, config)
    expect(capabilities).to_equal({})
