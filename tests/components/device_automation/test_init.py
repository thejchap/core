"""The test for light device automation."""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import attr
import voluptuous as vol

from tryke import Depends, expect, fixture, test

from homeassistant import loader
from homeassistant.components import automation, device_automation
from homeassistant.components.device_automation import (
    InvalidDeviceAutomationConfig,
    toggle_entity,
)
from homeassistant.components.websocket_api import TYPE_RESULT
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import IntegrationNotFound
from homeassistant.requirements import RequirementsNotFound
from homeassistant.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
    MockModule,
    async_mock_service,
    mock_integration,
    mock_platform,
)
from tests.hass_fixtures import (
    LogCapture,
    caplog as caplog_fixture,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
)
from tests.hass_tryke_helpers import expect_raises_async
from tests.typing import WebSocketGenerator


@attr.s(frozen=True, slots=True)
class MockDeviceEntry(dr.DeviceEntry):
    """Device Registry Entry with fixed UUID."""

    id: str = attr.ib(default="very_unique")


@fixture
async def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Dummy local fixture to opt into Tryke's HookExecutor path."""
    return hass


@fixture
def fake_integration(hass: HomeAssistant = Depends(_trigger_executor)) -> None:
    """Set up a mock integration with device automation support."""
    FAKE_DOMAIN = "fake_integration"

    hass.config.components.add(FAKE_DOMAIN)

    async def _async_get_actions(
        hass: HomeAssistant, device_id: str
    ) -> list[dict[str, str]]:
        """List device actions."""
        return await toggle_entity.async_get_actions(hass, device_id, FAKE_DOMAIN)

    async def _async_get_conditions(
        hass: HomeAssistant, device_id: str
    ) -> list[dict[str, str]]:
        """List device conditions."""
        return await toggle_entity.async_get_conditions(hass, device_id, FAKE_DOMAIN)

    async def _async_get_triggers(
        hass: HomeAssistant, device_id: str
    ) -> list[dict[str, str]]:
        """List device triggers."""
        return await toggle_entity.async_get_triggers(hass, device_id, FAKE_DOMAIN)

    mock_platform(
        hass,
        f"{FAKE_DOMAIN}.device_action",
        Mock(
            ACTION_SCHEMA=toggle_entity.ACTION_SCHEMA.extend(
                {vol.Required("domain"): FAKE_DOMAIN}
            ),
            async_get_actions=_async_get_actions,
            spec=["ACTION_SCHEMA", "async_get_actions"],
        ),
    )

    mock_platform(
        hass,
        f"{FAKE_DOMAIN}.device_condition",
        Mock(
            CONDITION_SCHEMA=toggle_entity.CONDITION_SCHEMA.extend(
                {vol.Required("domain"): FAKE_DOMAIN}
            ),
            async_get_conditions=_async_get_conditions,
            spec=["CONDITION_SCHEMA", "async_get_conditions"],
        ),
    )

    mock_platform(
        hass,
        f"{FAKE_DOMAIN}.device_trigger",
        Mock(
            TRIGGER_SCHEMA=vol.All(
                toggle_entity.TRIGGER_SCHEMA,
                vol.Schema(
                    {vol.Required("domain"): FAKE_DOMAIN}, extra=vol.ALLOW_EXTRA
                ),
            ),
            async_get_triggers=_async_get_triggers,
            spec=["TRIGGER_SCHEMA", "async_get_triggers"],
        ),
    )


@test
async def websocket_get_actions(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test we get the expected actions through websocket."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        "fake_integration", "test", "5678", device_id=device_entry.id
    )
    expected_actions = [
        {
            "domain": "fake_integration",
            "type": "turn_off",
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        },
        {
            "domain": "fake_integration",
            "type": "turn_on",
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        },
        {
            "domain": "fake_integration",
            "type": "toggle",
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        },
    ]

    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "device_automation/action/list", "device_id": device_entry.id}
    )
    msg = await client.receive_json()

    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    actions = msg["result"]
    expect(len(actions)).to_equal(len(expected_actions))
    for action in expected_actions:
        expect(action in actions).to_be(True)


@test
async def websocket_get_conditions(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test we get the expected conditions through websocket."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        "fake_integration", "test", "5678", device_id=device_entry.id
    )
    expected_conditions = [
        {
            "condition": "device",
            "domain": "fake_integration",
            "type": "is_off",
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        },
        {
            "condition": "device",
            "domain": "fake_integration",
            "type": "is_on",
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        },
    ]

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/condition/list",
            "device_id": device_entry.id,
        }
    )
    msg = await client.receive_json()

    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    conditions = msg["result"]
    expect(len(conditions)).to_equal(len(expected_conditions))
    for condition in expected_conditions:
        expect(condition in conditions).to_be(True)


@test
async def websocket_get_triggers(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test we get the expected triggers through websocket."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        "fake_integration", "test", "5678", device_id=device_entry.id
    )
    expected_triggers = [
        {
            "platform": "device",
            "domain": "fake_integration",
            "type": "changed_states",
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        },
        {
            "platform": "device",
            "domain": "fake_integration",
            "type": "turned_off",
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        },
        {
            "platform": "device",
            "domain": "fake_integration",
            "type": "turned_on",
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        },
    ]

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/trigger/list",
            "device_id": device_entry.id,
        }
    )
    msg = await client.receive_json()

    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    triggers = msg["result"]
    expect(len(triggers)).to_equal(len(expected_triggers))
    for trigger in expected_triggers:
        expect(trigger in triggers).to_be(True)


@test
async def websocket_get_action_capabilities(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test we get the expected action capabilities through websocket."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        "fake_integration", "test", "5678", device_id=device_entry.id
    )
    expected_capabilities = {
        "turn_on": {
            "extra_fields": [
                {"type": "string", "name": "code", "optional": True, "required": False}
            ]
        },
        "turn_off": {"extra_fields": []},
        "toggle": {"extra_fields": []},
    }

    async def _async_get_action_capabilities(
        hass: HomeAssistant, config: ConfigType
    ) -> dict[str, vol.Schema]:
        """List action capabilities."""
        if config["type"] == "turn_on":
            return {"extra_fields": vol.Schema({vol.Optional("code"): str})}
        return {}

    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_action"]
    module.async_get_action_capabilities = _async_get_action_capabilities

    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "device_automation/action/list", "device_id": device_entry.id}
    )
    msg = await client.receive_json()

    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    actions = msg["result"]

    msg_id = 2
    expect(len(actions)).to_equal(3)
    for action in actions:
        await client.send_json(
            {
                "id": msg_id,
                "type": "device_automation/action/capabilities",
                "action": action,
            }
        )
        msg = await client.receive_json()
        expect(msg["id"]).to_equal(msg_id)
        expect(msg["type"]).to_equal(TYPE_RESULT)
        expect(msg["success"]).to_be_truthy()
        capabilities = msg["result"]
        expect(capabilities).to_equal(expected_capabilities[action["type"]])
        msg_id = msg_id + 1


@test
async def websocket_get_action_capabilities_unknown_domain(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get no action capabilities for a non existing domain."""
    await async_setup_component(hass, "device_automation", {})
    expected_capabilities = {}

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/action/capabilities",
            "action": {"domain": "beer"},
        }
    )
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    capabilities = msg["result"]
    expect(capabilities).to_equal(expected_capabilities)


@test
async def websocket_get_action_capabilities_no_capabilities(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test we get no action capabilities for a domain which has none.

    The tests tests a domain which has a device action platform, but no
    async_get_action_capabilities.
    """
    await async_setup_component(hass, "device_automation", {})
    expected_capabilities = {}

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/action/capabilities",
            "action": {"domain": "fake_integration"},
        }
    )
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    capabilities = msg["result"]
    expect(capabilities).to_equal(expected_capabilities)


@test
async def websocket_get_action_capabilities_bad_action(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test we get no action capabilities when there is an error."""
    await async_setup_component(hass, "device_automation", {})
    expected_capabilities = {}

    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_action"]
    module.async_get_action_capabilities = Mock(
        side_effect=InvalidDeviceAutomationConfig
    )

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/action/capabilities",
            "action": {"domain": "fake_integration"},
        }
    )
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    capabilities = msg["result"]
    expect(capabilities).to_equal(expected_capabilities)
    module.async_get_action_capabilities.assert_called_once()


@test
async def websocket_get_condition_capabilities(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test we get the expected condition capabilities through websocket."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        "fake_integration", "test", "5678", device_id=device_entry.id
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

    async def _async_get_condition_capabilities(
        hass: HomeAssistant, config: ConfigType
    ) -> dict[str, vol.Schema]:
        """List condition capabilities."""
        return await toggle_entity.async_get_condition_capabilities(hass, config)

    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_condition"]
    module.async_get_condition_capabilities = _async_get_condition_capabilities

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/condition/list",
            "device_id": device_entry.id,
        }
    )
    msg = await client.receive_json()

    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    conditions = msg["result"]

    msg_id = 2
    expect(len(conditions)).to_equal(2)
    for condition in conditions:
        await client.send_json(
            {
                "id": msg_id,
                "type": "device_automation/condition/capabilities",
                "condition": condition,
            }
        )
        msg = await client.receive_json()
        expect(msg["id"]).to_equal(msg_id)
        expect(msg["type"]).to_equal(TYPE_RESULT)
        expect(msg["success"]).to_be_truthy()
        capabilities = msg["result"]
        expect(capabilities).to_equal(expected_capabilities)
        msg_id = msg_id + 1


@test
async def websocket_get_condition_capabilities_unknown_domain(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get no condition capabilities for a non existing domain."""
    await async_setup_component(hass, "device_automation", {})
    expected_capabilities = {}

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/condition/capabilities",
            "condition": {"condition": "device", "domain": "beer", "device_id": "1234"},
        }
    )
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    capabilities = msg["result"]
    expect(capabilities).to_equal(expected_capabilities)


@test
async def websocket_get_condition_capabilities_no_capabilities(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test we get no condition capabilities for a domain which has none.

    The tests tests a domain which has a device condition platform, but no
    async_get_condition_capabilities.
    """
    await async_setup_component(hass, "device_automation", {})
    expected_capabilities = {}

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/condition/capabilities",
            "condition": {
                "condition": "device",
                "device_id": "abcd",
                "domain": "fake_integration",
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    capabilities = msg["result"]
    expect(capabilities).to_equal(expected_capabilities)


@test
async def websocket_get_condition_capabilities_bad_condition(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test we get no condition capabilities when there is an error."""
    await async_setup_component(hass, "device_automation", {})
    expected_capabilities = {}

    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_condition"]
    module.async_get_condition_capabilities = Mock(
        side_effect=InvalidDeviceAutomationConfig
    )

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/condition/capabilities",
            "condition": {
                "condition": "device",
                "device_id": "abcd",
                "domain": "fake_integration",
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    capabilities = msg["result"]
    expect(capabilities).to_equal(expected_capabilities)
    module.async_get_condition_capabilities.assert_called_once()


@test
async def async_get_device_automations_single_device_trigger(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get can fetch the triggers for a device id."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        "light", "test", "5678", device_id=device_entry.id
    )
    result = await device_automation.async_get_device_automations(
        hass, device_automation.DeviceAutomationType.TRIGGER, [device_entry.id]
    )
    expect(device_entry.id in result).to_be(True)
    expect(len(result[device_entry.id])).to_equal(3)


@test
async def async_get_device_automations_all_devices_trigger(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get can fetch all the triggers when no device id is passed."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        "light", "test", "5678", device_id=device_entry.id
    )
    result = await device_automation.async_get_device_automations(
        hass, device_automation.DeviceAutomationType.TRIGGER
    )
    expect(device_entry.id in result).to_be(True)
    expect(len(result[device_entry.id])).to_equal(3)  # toggled, turned_on, turned_off


@test
async def async_get_device_automations_all_devices_condition(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get can fetch all the conditions when no device id is passed."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        "light", "test", "5678", device_id=device_entry.id
    )
    result = await device_automation.async_get_device_automations(
        hass, device_automation.DeviceAutomationType.CONDITION
    )
    expect(device_entry.id in result).to_be(True)
    expect(len(result[device_entry.id])).to_equal(2)


@test
async def async_get_device_automations_all_devices_action(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get can fetch all the actions when no device id is passed."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        "light", "test", "5678", device_id=device_entry.id
    )
    result = await device_automation.async_get_device_automations(
        hass, device_automation.DeviceAutomationType.ACTION
    )
    expect(device_entry.id in result).to_be(True)
    expect(len(result[device_entry.id])).to_equal(3)


@test
async def async_get_device_automations_all_devices_action_exception_throw(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test we get can fetch all the actions when no device id is passed and can handle one throwing an exception."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        "light", "test", "5678", device_id=device_entry.id
    )
    with patch(
        "homeassistant.components.light.device_trigger.async_get_triggers",
        side_effect=KeyError,
    ):
        result = await device_automation.async_get_device_automations(
            hass, device_automation.DeviceAutomationType.TRIGGER
        )
    expect(device_entry.id in result).to_be(True)
    expect(len(result[device_entry.id])).to_equal(0)
    expect("KeyError" in caplog.text).to_be(True)


@test.cases(
    test.case("trigger", trigger_key="trigger"),
    test.case("platform", trigger_key="platform"),
)
async def websocket_get_trigger_capabilities(
    *,
    trigger_key: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test we get the expected trigger capabilities through websocket."""
    await async_setup_component(hass, "device_automation", {})
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        "fake_integration", "test", "5678", device_id=device_entry.id
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

    async def _async_get_trigger_capabilities(
        hass: HomeAssistant, config: ConfigType
    ) -> dict[str, vol.Schema]:
        """List trigger capabilities."""
        return await toggle_entity.async_get_trigger_capabilities(hass, config)

    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_trigger"]
    module.async_get_trigger_capabilities = _async_get_trigger_capabilities

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/trigger/list",
            "device_id": device_entry.id,
        }
    )
    msg = await client.receive_json()

    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    triggers: dict = msg["result"]

    msg_id = 2
    expect(len(triggers)).to_equal(3)  # toggled, turned_on, turned_off
    for trigger in triggers:
        trigger[trigger_key] = trigger.pop("platform")
        await client.send_json(
            {
                "id": msg_id,
                "type": "device_automation/trigger/capabilities",
                "trigger": trigger,
            }
        )
        msg = await client.receive_json()
        expect(msg["id"]).to_equal(msg_id)
        expect(msg["type"]).to_equal(TYPE_RESULT)
        expect(msg["success"]).to_be_truthy()
        capabilities = msg["result"]
        expect(capabilities).to_equal(expected_capabilities)
        msg_id = msg_id + 1


@test
async def websocket_get_trigger_capabilities_unknown_domain(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get no trigger capabilities for a non existing domain."""
    await async_setup_component(hass, "device_automation", {})
    expected_capabilities = {}

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/trigger/capabilities",
            "trigger": {"platform": "device", "domain": "beer", "device_id": "abcd"},
        }
    )
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    capabilities = msg["result"]
    expect(capabilities).to_equal(expected_capabilities)


@test
async def websocket_get_trigger_capabilities_no_capabilities(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test we get no trigger capabilities for a domain which has none.

    The tests tests a domain which has a device trigger platform, but no
    async_get_trigger_capabilities.
    """
    await async_setup_component(hass, "device_automation", {})
    expected_capabilities = {}

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/trigger/capabilities",
            "trigger": {
                "platform": "device",
                "device_id": "abcd",
                "domain": "fake_integration",
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    capabilities = msg["result"]
    expect(capabilities).to_equal(expected_capabilities)


@test
async def websocket_get_trigger_capabilities_bad_trigger(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test we get no trigger capabilities when there is an error."""
    await async_setup_component(hass, "device_automation", {})
    expected_capabilities = {}

    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_trigger"]
    module.async_get_trigger_capabilities = Mock(
        side_effect=InvalidDeviceAutomationConfig
    )

    client = await hass_ws_client(hass)
    await client.send_json(
        {
            "id": 1,
            "type": "device_automation/trigger/capabilities",
            "trigger": {
                "platform": "device",
                "device_id": "abcd",
                "domain": "fake_integration",
            },
        }
    )
    msg = await client.receive_json()
    expect(msg["id"]).to_equal(1)
    expect(msg["type"]).to_equal(TYPE_RESULT)
    expect(msg["success"]).to_be_truthy()
    capabilities = msg["result"]
    expect(capabilities).to_equal(expected_capabilities)
    module.async_get_trigger_capabilities.assert_called_once()


@test
async def automation_with_non_existing_integration(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test device automation trigger with non existing integration."""
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {
                        "platform": "device",
                        "device_id": "none",
                        "domain": "beer",
                    },
                    "action": {
                        "service": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()

    expect("Integration 'beer' not found" in caplog.text).to_be(True)


@test
async def automation_with_device_action(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test automation with a device action."""
    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_action"]
    module.async_call_action_from_config = AsyncMock()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        "fake_integration", "test", "5678", device_id=device_entry.id
    )

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "action": {
                        "device_id": device_entry.id,
                        "domain": "fake_integration",
                        "entity_id": entity_entry.id,
                        "type": "turn_on",
                    },
                }
            },
        )
    ).to_be_truthy()

    module.async_call_action_from_config.assert_not_called()

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()

    module.async_call_action_from_config.assert_awaited_once()


@test
async def automation_with_dynamically_validated_action(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test device automation with an action which is dynamically validated."""
    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_action"]
    module.async_validate_action_config = AsyncMock()

    config_entry = MockConfigEntry(domain="fake_integration", data={})
    config_entry.mock_state(hass, ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "action": {
                        "device_id": device_entry.id,
                        "domain": "fake_integration",
                    },
                }
            },
        )
    ).to_be_truthy()

    module.async_validate_action_config.assert_awaited_once()


@test
async def automation_with_integration_without_device_action(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test device automation action with integration without device action support."""
    mock_integration(hass, MockModule(domain="test"))
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "action": {"device_id": "", "domain": "test"},
                }
            },
        )
    ).to_be_truthy()

    expect(
        "Integration 'test' does not support device automation actions" in caplog.text
    ).to_be(True)


@test
async def automation_with_device_condition(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test automation with a device condition."""
    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_condition"]
    module.async_condition_from_config = Mock()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        "fake_integration", "test", "5678", device_id=device_entry.id
    )

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": {
                        "condition": "device",
                        "device_id": device_entry.id,
                        "domain": "fake_integration",
                        "entity_id": entity_entry.id,
                        "type": "is_on",
                    },
                    "action": {
                        "service": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()

    module.async_condition_from_config.assert_called_once()


@test
async def automation_with_dynamically_validated_condition(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test device automation with a condition which is dynamically validated."""
    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_condition"]
    module.async_validate_condition_config = AsyncMock(return_value=MagicMock())

    config_entry = MockConfigEntry(domain="fake_integration", data={})
    config_entry.mock_state(hass, ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": {
                        "condition": "device",
                        "device_id": device_entry.id,
                        "domain": "fake_integration",
                    },
                    "action": {
                        "service": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()

    module.async_validate_condition_config.assert_awaited_once()


@test
async def automation_with_integration_without_device_condition(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test device automation condition with integration without device condition support."""
    mock_integration(hass, MockModule(domain="test"))
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {"platform": "event", "event_type": "test_event1"},
                    "condition": {
                        "condition": "device",
                        "device_id": "none",
                        "domain": "test",
                    },
                    "action": {
                        "service": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()

    expect(
        "Integration 'test' does not support device automation conditions"
        in caplog.text
    ).to_be(True)


@test
async def automation_with_device_trigger(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test automation with a device trigger."""
    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_trigger"]
    module.async_attach_trigger = AsyncMock()

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        "fake_integration", "test", "5678", device_id=device_entry.id
    )

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {
                        "platform": "device",
                        "device_id": device_entry.id,
                        "domain": "fake_integration",
                        "entity_id": entity_entry.id,
                        "type": "turned_off",
                    },
                    "action": {
                        "service": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()

    module.async_attach_trigger.assert_awaited_once()


@test
async def automation_with_dynamically_validated_trigger(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test device automation with a trigger which is dynamically validated."""
    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_trigger"]
    module.async_attach_trigger = AsyncMock()
    module.async_validate_trigger_config = AsyncMock(wraps=lambda hass, config: config)

    config_entry = MockConfigEntry(domain="fake_integration", data={})
    config_entry.mock_state(hass, ConfigEntryState.LOADED)
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        "fake_integration", "test", "5678", device_id=device_entry.id
    )

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {
                        "platform": "device",
                        "device_id": device_entry.id,
                        "domain": "fake_integration",
                    },
                    "action": {
                        "service": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()

    module.async_validate_trigger_config.assert_awaited_once()
    module.async_attach_trigger.assert_awaited_once()


@test
async def automation_with_integration_without_device_trigger(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
) -> None:
    """Test device automation trigger with integration without device trigger support."""
    mock_integration(hass, MockModule(domain="test"))
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {
                        "platform": "device",
                        "device_id": "none",
                        "domain": "test",
                    },
                    "action": {
                        "service": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()

    expect(
        "Integration 'test' does not support device automation triggers" in caplog.text
    ).to_be(True)


BAD_AUTOMATIONS = [
    (
        {"device_id": "very_unique", "domain": "light"},
        "required key not provided @ data['entity_id']",
    ),
    (
        {"device_id": "wrong", "domain": "light"},
        "Unknown device 'wrong'",
    ),
    (
        {"device_id": "wrong"},
        "required key not provided @ data{path}['domain']",
    ),
    (
        {"device_id": "wrong", "domain": "light"},
        "Unknown device 'wrong'",
    ),
    (
        {"device_id": "very_unique", "domain": "light"},
        "required key not provided @ data['entity_id']",
    ),
    (
        {"device_id": "very_unique", "domain": "light", "entity_id": "wrong"},
        "Unknown entity 'wrong'",
    ),
]

BAD_TRIGGERS = BAD_CONDITIONS = [
    *BAD_AUTOMATIONS,
    ({"domain": "light"}, "required key not provided @ data{path}['device_id']"),
]


@test.cases(
    *(
        test.case(f"case_{i}", action=action, expected_error=expected_error)
        for i, (action, expected_error) in enumerate(BAD_AUTOMATIONS)
    )
)
async def automation_with_bad_action(
    *,
    action: dict[str, str],
    expected_error: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test automation with bad device action."""
    with patch(
        "homeassistant.helpers.device_registry.DeviceEntry", MockDeviceEntry
    ):
        config_entry = MockConfigEntry(domain="fake_integration", data={})
        config_entry.mock_state(hass, ConfigEntryState.LOADED)
        config_entry.add_to_hass(hass)
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        )

        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "alias": "hello",
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event1",
                        },
                        "action": action,
                    }
                },
            )
        ).to_be_truthy()

    expect(expected_error.format(path="['actions'][0]") in caplog.text).to_be(True)


@test.cases(
    *(
        test.case(f"case_{i}", condition=condition, expected_error=expected_error)
        for i, (condition, expected_error) in enumerate(BAD_CONDITIONS)
    )
)
async def automation_with_bad_condition_action(
    *,
    condition: dict[str, str],
    expected_error: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test automation with bad device action."""
    with patch(
        "homeassistant.helpers.device_registry.DeviceEntry", MockDeviceEntry
    ):
        config_entry = MockConfigEntry(domain="fake_integration", data={})
        config_entry.mock_state(hass, ConfigEntryState.LOADED)
        config_entry.add_to_hass(hass)
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        )

        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "alias": "hello",
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event1",
                        },
                        "action": {"condition": "device"} | condition,
                    }
                },
            )
        ).to_be_truthy()

    expect(expected_error.format(path="['actions'][0]") in caplog.text).to_be(True)


@test.cases(
    *(
        test.case(f"case_{i}", condition=condition, expected_error=expected_error)
        for i, (condition, expected_error) in enumerate(BAD_CONDITIONS)
    )
)
async def automation_with_bad_condition(
    *,
    condition: dict[str, str],
    expected_error: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test automation with bad device condition."""
    with patch(
        "homeassistant.helpers.device_registry.DeviceEntry", MockDeviceEntry
    ):
        config_entry = MockConfigEntry(domain="fake_integration", data={})
        config_entry.mock_state(hass, ConfigEntryState.LOADED)
        config_entry.add_to_hass(hass)
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        )

        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "alias": "hello",
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event1",
                        },
                        "condition": {"condition": "device"} | condition,
                        "action": {
                            "service": "test.automation",
                            "entity_id": "hello.world",
                        },
                    }
                },
            )
        ).to_be_truthy()

    expect(expected_error.format(path="['conditions'][0]") in caplog.text).to_be(True)


@test
async def automation_with_sub_condition(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test automation with device condition under and/or conditions."""
    service_calls = async_mock_service(hass, "test", "automation")
    LIGHT_DOMAIN = "light"

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry1 = entity_registry.async_get_or_create(
        "fake_integration", "test", "0001", device_id=device_entry.id
    )
    entity_entry2 = entity_registry.async_get_or_create(
        "fake_integration", "test", "0002", device_id=device_entry.id
    )

    hass.states.async_set(entity_entry1.entity_id, STATE_ON)
    hass.states.async_set(entity_entry2.entity_id, STATE_OFF)

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
                        "condition": [
                            {
                                "condition": "and",
                                "conditions": [
                                    {
                                        "condition": "device",
                                        "domain": LIGHT_DOMAIN,
                                        "device_id": device_entry.id,
                                        "entity_id": entity_entry1.id,
                                        "type": "is_on",
                                    },
                                    {
                                        "condition": "device",
                                        "domain": LIGHT_DOMAIN,
                                        "device_id": device_entry.id,
                                        "entity_id": entity_entry2.id,
                                        "type": "is_on",
                                    },
                                ],
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "and {{ trigger.platform }}"
                                    " - {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event1",
                        },
                        "condition": [
                            {
                                "condition": "or",
                                "conditions": [
                                    {
                                        "condition": "device",
                                        "domain": LIGHT_DOMAIN,
                                        "device_id": device_entry.id,
                                        "entity_id": entity_entry1.id,
                                        "type": "is_on",
                                    },
                                    {
                                        "condition": "device",
                                        "domain": LIGHT_DOMAIN,
                                        "device_id": device_entry.id,
                                        "entity_id": entity_entry2.id,
                                        "type": "is_on",
                                    },
                                ],
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "or {{ trigger.platform }}"
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
    expect(hass.states.get(entity_entry1.entity_id).state).to_equal(STATE_ON)
    expect(hass.states.get(entity_entry2.entity_id).state).to_equal(STATE_OFF)
    expect(len(service_calls)).to_equal(0)

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("or event - test_event1")

    hass.states.async_set(entity_entry1.entity_id, STATE_OFF)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.states.async_set(entity_entry2.entity_id, STATE_ON)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal("or event - test_event1")

    hass.states.async_set(entity_entry1.entity_id, STATE_ON)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(4)
    expect(
        sorted([service_calls[2].data["some"], service_calls[3].data["some"]])
    ).to_equal(sorted(["or event - test_event1", "and event - test_event1"]))


@test.cases(
    *(
        test.case(f"case_{i}", condition=condition, expected_error=expected_error)
        for i, (condition, expected_error) in enumerate(BAD_CONDITIONS)
    )
)
async def automation_with_bad_sub_condition(
    *,
    condition: dict[str, str],
    expected_error: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test automation with bad device condition under and/or conditions."""
    with patch(
        "homeassistant.helpers.device_registry.DeviceEntry", MockDeviceEntry
    ):
        config_entry = MockConfigEntry(domain="fake_integration", data={})
        config_entry.mock_state(hass, ConfigEntryState.LOADED)
        config_entry.add_to_hass(hass)
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        )

        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "alias": "hello",
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event1",
                        },
                        "condition": {
                            "condition": "and",
                            "conditions": [{"condition": "device"} | condition],
                        },
                        "action": {
                            "service": "test.automation",
                            "entity_id": "hello.world",
                        },
                    }
                },
            )
        ).to_be_truthy()

    path = "['conditions'][0]['conditions'][0]"
    expect(expected_error.format(path=path) in caplog.text).to_be(True)


@test.cases(
    *(
        test.case(f"case_{i}", trigger=trigger, expected_error=expected_error)
        for i, (trigger, expected_error) in enumerate(BAD_TRIGGERS)
    )
)
async def automation_with_bad_trigger(
    *,
    trigger: dict[str, str],
    expected_error: str,
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test automation with bad device trigger."""
    with patch(
        "homeassistant.helpers.device_registry.DeviceEntry", MockDeviceEntry
    ):
        config_entry = MockConfigEntry(domain="fake_integration", data={})
        config_entry.mock_state(hass, ConfigEntryState.LOADED)
        config_entry.add_to_hass(hass)
        device_registry.async_get_or_create(
            config_entry_id=config_entry.entry_id,
            connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
        )

        expect(
            await async_setup_component(
                hass,
                automation.DOMAIN,
                {
                    automation.DOMAIN: {
                        "alias": "hello",
                        "trigger": {"platform": "device"} | trigger,
                        "action": {
                            "service": "test.automation",
                            "entity_id": "hello.world",
                        },
                    }
                },
            )
        ).to_be_truthy()

    expect(expected_error.format(path="") in caplog.text).to_be(True)


@test
async def websocket_device_not_found(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
) -> None:
    """Test calling command with unknown device."""
    await async_setup_component(hass, "device_automation", {})
    client = await hass_ws_client(hass)
    await client.send_json(
        {"id": 1, "type": "device_automation/action/list", "device_id": "non-existing"}
    )
    msg = await client.receive_json()

    expect(msg["id"]).to_equal(1)
    expect(msg["success"]).to_be_falsy()
    expect(msg["error"]).to_equal(
        {"code": "not_found", "message": "Device not found"}
    )


@test
async def automation_with_unknown_device(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test device automation with a trigger with an unknown device."""
    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_trigger"]
    module.async_validate_trigger_config = AsyncMock()

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {
                        "platform": "device",
                        "device_id": "no_such_device",
                        "domain": "fake_integration",
                    },
                    "action": {
                        "service": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()

    module.async_validate_trigger_config.assert_not_awaited()
    expect(
        "Automation with alias 'hello' failed to setup triggers and has been disabled: "
        "Unknown device 'no_such_device'" in caplog.text
    ).to_be(True)


@test
async def automation_with_device_wrong_domain(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test device automation where the device doesn't have the right config entry."""
    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_trigger"]
    module.async_validate_trigger_config = AsyncMock()

    source_config_entry = MockConfigEntry(domain="not_fake_integration")
    source_config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=source_config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {
                        "platform": "device",
                        "device_id": device_entry.id,
                        "domain": "fake_integration",
                    },
                    "action": {
                        "service": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()

    module.async_validate_trigger_config.assert_not_awaited()
    expect(
        "Automation with alias 'hello' failed to setup triggers and has been disabled: "
        f"Device '{device_entry.id}' has no config entry from domain 'fake_integration'"
        in caplog.text
    ).to_be(True)


@test
async def automation_with_device_component_not_loaded(
    hass: HomeAssistant = Depends(_trigger_executor),
    caplog: LogCapture = Depends(caplog_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    fake_integration: None = Depends(fake_integration),
) -> None:
    """Test device automation where the device's config entry is not loaded."""
    module_cache = hass.data[loader.DATA_COMPONENTS]
    module = module_cache["fake_integration.device_trigger"]
    module.async_validate_trigger_config = AsyncMock()
    module.async_attach_trigger = AsyncMock()

    config_entry = MockConfigEntry(domain="fake_integration", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: {
                    "alias": "hello",
                    "trigger": {
                        "platform": "device",
                        "device_id": device_entry.id,
                        "domain": "fake_integration",
                    },
                    "action": {
                        "service": "test.automation",
                        "entity_id": "hello.world",
                    },
                }
            },
        )
    ).to_be_truthy()

    module.async_validate_trigger_config.assert_not_awaited()


@test.cases(
    test.case("integration_not_found", exc=IntegrationNotFound("test")),
    test.case("requirements_not_found", exc=RequirementsNotFound("test", [])),
    test.case("import_error", exc=ImportError("test")),
)
async def async_get_device_automations_platform_reraises_exceptions(
    *,
    exc: Exception,
    hass: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test InvalidDeviceAutomationConfig is raised when async_get_integration_with_requirements fails."""
    await async_setup_component(hass, "device_automation", {})
    with patch(
        "homeassistant.components.device_automation.async_get_integration_with_requirements",
        side_effect=exc,
    ):
        async with expect_raises_async(InvalidDeviceAutomationConfig):
            await device_automation.async_get_device_automation_platform(
                hass, "test", device_automation.DeviceAutomationType.TRIGGER
            )
