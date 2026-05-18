"""The tests for Alarm control panel device actions (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.alarm_control_panel import (
    DOMAIN,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.const import CONF_PLATFORM, STATE_UNKNOWN, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import mock_alarm_control_panel_entities as mock_acp_entities_fixture
from .common import MockAlarm

from tests.common import (
    MockConfigEntry,
    async_get_device_automation_capabilities,
    async_get_device_automations,
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


@test.cases(
    test.case(
        "noset_none",
        set_state=False,
        features_reg=0,
        features_state=0,
        expected_action_types=["disarm"],
    ),
    test.case(
        "noset_arm_away",
        set_state=False,
        features_reg=AlarmControlPanelEntityFeature.ARM_AWAY,
        features_state=0,
        expected_action_types=["disarm", "arm_away"],
    ),
    test.case(
        "noset_arm_home",
        set_state=False,
        features_reg=AlarmControlPanelEntityFeature.ARM_HOME,
        features_state=0,
        expected_action_types=["disarm", "arm_home"],
    ),
    test.case(
        "noset_arm_night",
        set_state=False,
        features_reg=AlarmControlPanelEntityFeature.ARM_NIGHT,
        features_state=0,
        expected_action_types=["disarm", "arm_night"],
    ),
    test.case(
        "noset_trigger",
        set_state=False,
        features_reg=AlarmControlPanelEntityFeature.TRIGGER,
        features_state=0,
        expected_action_types=["disarm", "trigger"],
    ),
    test.case(
        "set_none",
        set_state=True,
        features_reg=0,
        features_state=0,
        expected_action_types=["disarm"],
    ),
    test.case(
        "set_arm_away",
        set_state=True,
        features_reg=0,
        features_state=AlarmControlPanelEntityFeature.ARM_AWAY,
        expected_action_types=["disarm", "arm_away"],
    ),
    test.case(
        "set_arm_home",
        set_state=True,
        features_reg=0,
        features_state=AlarmControlPanelEntityFeature.ARM_HOME,
        expected_action_types=["disarm", "arm_home"],
    ),
    test.case(
        "set_arm_night",
        set_state=True,
        features_reg=0,
        features_state=AlarmControlPanelEntityFeature.ARM_NIGHT,
        expected_action_types=["disarm", "arm_night"],
    ),
    test.case(
        "set_arm_vacation",
        set_state=True,
        features_reg=0,
        features_state=AlarmControlPanelEntityFeature.ARM_VACATION,
        expected_action_types=["disarm", "arm_vacation"],
    ),
    test.case(
        "set_trigger",
        set_state=True,
        features_reg=0,
        features_state=AlarmControlPanelEntityFeature.TRIGGER,
        expected_action_types=["disarm", "trigger"],
    ),
)
async def get_actions(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    set_state: bool,
    features_reg: int,
    features_state: int,
    expected_action_types: list[str],
) -> None:
    """Test we get the expected actions from an alarm_control_panel."""
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
        supported_features=features_reg,
    )
    if set_state:
        hass.states.async_set(
            f"{DOMAIN}.test_5678", "attributes", {"supported_features": features_state}
        )
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": action,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
        for action in expected_action_types
    ]
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(actions).to_equal(unordered(expected_actions))


@test.cases(
    test.case(
        "integration",
        hidden_by=er.RegistryEntryHider.INTEGRATION,
        entity_category=None,
    ),
    test.case(
        "user",
        hidden_by=er.RegistryEntryHider.USER,
        entity_category=None,
    ),
    test.case(
        "config",
        hidden_by=None,
        entity_category=EntityCategory.CONFIG,
    ),
    test.case(
        "diagnostic",
        hidden_by=None,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)
async def get_actions_hidden_auxiliary(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    hidden_by: er.RegistryEntryHider | None,
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
        supported_features=AlarmControlPanelEntityFeature.ARM_AWAY,
    )
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": action,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": True},
        }
        for action in ("disarm", "arm_away")
    ]
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(actions).to_equal(unordered(expected_actions))


@test
async def get_actions_arm_night_only(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected actions from an alarm_control_panel."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )
    hass.states.async_set(
        "alarm_control_panel.test_5678", "attributes", {"supported_features": 4}
    )
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": "arm_night",
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        },
        {
            "domain": DOMAIN,
            "type": "disarm",
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        },
    ]
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(actions).to_equal(unordered(expected_actions))


@test
async def get_action_capabilities(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_alarm_control_panel_entities: dict[str, MockAlarm] = Depends(
        mock_acp_entities_fixture
    ),
) -> None:
    """Test we get the expected capabilities from a sensor trigger."""
    setup_test_component_platform(
        hass, DOMAIN, mock_alarm_control_panel_entities.values()
    )
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
    entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_alarm_control_panel_entities["no_arm_code"].unique_id,
        device_id=device_entry.id,
    )

    expected_capabilities = {
        "arm_away": {"extra_fields": []},
        "arm_home": {"extra_fields": []},
        "arm_night": {"extra_fields": []},
        "arm_vacation": {"extra_fields": []},
        "disarm": {
            "extra_fields": [
                {"name": "code", "optional": True, "required": False, "type": "string"}
            ]
        },
        "trigger": {"extra_fields": []},
    }
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(len(actions)).to_equal(6)
    expect({action["type"] for action in actions}).to_equal(set(expected_capabilities))
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        expect(capabilities).to_equal(expected_capabilities[action["type"]])


@test
async def get_action_capabilities_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_alarm_control_panel_entities: dict[str, MockAlarm] = Depends(
        mock_acp_entities_fixture
    ),
) -> None:
    """Test we get the expected capabilities from a sensor trigger."""
    setup_test_component_platform(
        hass, DOMAIN, mock_alarm_control_panel_entities.values()
    )
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
    entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_alarm_control_panel_entities["no_arm_code"].unique_id,
        device_id=device_entry.id,
    )

    expected_capabilities = {
        "arm_away": {"extra_fields": []},
        "arm_home": {"extra_fields": []},
        "arm_night": {"extra_fields": []},
        "arm_vacation": {"extra_fields": []},
        "disarm": {
            "extra_fields": [
                {"name": "code", "optional": True, "required": False, "type": "string"}
            ]
        },
        "trigger": {"extra_fields": []},
    }
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(len(actions)).to_equal(6)
    expect({action["type"] for action in actions}).to_equal(set(expected_capabilities))
    for action in actions:
        action["entity_id"] = entity_registry.async_get(action["entity_id"]).entity_id
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        expect(capabilities).to_equal(expected_capabilities[action["type"]])


@test
async def get_action_capabilities_arm_code(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_alarm_control_panel_entities: dict[str, MockAlarm] = Depends(
        mock_acp_entities_fixture
    ),
) -> None:
    """Test we get the expected capabilities from a sensor trigger."""
    setup_test_component_platform(
        hass, DOMAIN, mock_alarm_control_panel_entities.values()
    )
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
    entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_alarm_control_panel_entities["arm_code"].unique_id,
        device_id=device_entry.id,
    )

    expected_capabilities = {
        "arm_away": {
            "extra_fields": [
                {"name": "code", "optional": True, "required": False, "type": "string"}
            ]
        },
        "arm_home": {
            "extra_fields": [
                {"name": "code", "optional": True, "required": False, "type": "string"}
            ]
        },
        "arm_night": {
            "extra_fields": [
                {"name": "code", "optional": True, "required": False, "type": "string"}
            ]
        },
        "arm_vacation": {
            "extra_fields": [
                {"name": "code", "optional": True, "required": False, "type": "string"}
            ]
        },
        "disarm": {
            "extra_fields": [
                {"name": "code", "optional": True, "required": False, "type": "string"}
            ]
        },
        "trigger": {"extra_fields": []},
    }
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(len(actions)).to_equal(6)
    expect({action["type"] for action in actions}).to_equal(set(expected_capabilities))
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        expect(capabilities).to_equal(expected_capabilities[action["type"]])


@test
async def get_action_capabilities_arm_code_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_alarm_control_panel_entities: dict[str, MockAlarm] = Depends(
        mock_acp_entities_fixture
    ),
) -> None:
    """Test we get the expected capabilities from a sensor trigger."""
    setup_test_component_platform(
        hass, DOMAIN, mock_alarm_control_panel_entities.values()
    )
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
    entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_alarm_control_panel_entities["arm_code"].unique_id,
        device_id=device_entry.id,
    )

    expected_capabilities = {
        "arm_away": {
            "extra_fields": [
                {"name": "code", "optional": True, "required": False, "type": "string"}
            ]
        },
        "arm_home": {
            "extra_fields": [
                {"name": "code", "optional": True, "required": False, "type": "string"}
            ]
        },
        "arm_night": {
            "extra_fields": [
                {"name": "code", "optional": True, "required": False, "type": "string"}
            ]
        },
        "arm_vacation": {
            "extra_fields": [
                {"name": "code", "optional": True, "required": False, "type": "string"}
            ]
        },
        "disarm": {
            "extra_fields": [
                {"name": "code", "optional": True, "required": False, "type": "string"}
            ]
        },
        "trigger": {"extra_fields": []},
    }
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(len(actions)).to_equal(6)
    expect({action["type"] for action in actions}).to_equal(set(expected_capabilities))
    for action in actions:
        action["entity_id"] = entity_registry.async_get(action["entity_id"]).entity_id
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        expect(capabilities).to_equal(expected_capabilities[action["type"]])


@test
async def action(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_alarm_control_panel_entities: dict[str, MockAlarm] = Depends(
        mock_acp_entities_fixture
    ),
) -> None:
    """Test for turn_on and turn_off actions."""
    setup_test_component_platform(
        hass, DOMAIN, mock_alarm_control_panel_entities.values()
    )

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_alarm_control_panel_entities["no_arm_code"].unique_id,
        device_id=device_entry.id,
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
                            "event_type": "test_event_arm_away",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entity_entry.id,
                            "type": "arm_away",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_arm_home",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entity_entry.id,
                            "type": "arm_home",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_arm_night",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entity_entry.id,
                            "type": "arm_night",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_arm_vacation",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entity_entry.id,
                            "type": "arm_vacation",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_disarm",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entity_entry.id,
                            "type": "disarm",
                            "code": "1234",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_trigger",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entity_entry.id,
                            "type": "trigger",
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(hass.states.get(entity_entry.entity_id).state).to_equal(STATE_UNKNOWN)

    hass.bus.async_fire("test_event_arm_away")
    await hass.async_block_till_done()
    expect(hass.states.get(entity_entry.entity_id).state).to_equal(
        AlarmControlPanelState.ARMED_AWAY
    )

    hass.bus.async_fire("test_event_arm_home")
    await hass.async_block_till_done()
    expect(hass.states.get(entity_entry.entity_id).state).to_equal(
        AlarmControlPanelState.ARMED_HOME
    )

    hass.bus.async_fire("test_event_arm_vacation")
    await hass.async_block_till_done()
    expect(hass.states.get(entity_entry.entity_id).state).to_equal(
        AlarmControlPanelState.ARMED_VACATION
    )

    hass.bus.async_fire("test_event_arm_night")
    await hass.async_block_till_done()
    expect(hass.states.get(entity_entry.entity_id).state).to_equal(
        AlarmControlPanelState.ARMED_NIGHT
    )

    hass.bus.async_fire("test_event_disarm")
    await hass.async_block_till_done()
    expect(hass.states.get(entity_entry.entity_id).state).to_equal(
        AlarmControlPanelState.DISARMED
    )

    hass.bus.async_fire("test_event_trigger")
    await hass.async_block_till_done()
    expect(hass.states.get(entity_entry.entity_id).state).to_equal(
        AlarmControlPanelState.TRIGGERED
    )


@test
async def action_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_alarm_control_panel_entities: dict[str, MockAlarm] = Depends(
        mock_acp_entities_fixture
    ),
) -> None:
    """Test for turn_on and turn_off actions."""
    setup_test_component_platform(
        hass, DOMAIN, mock_alarm_control_panel_entities.values()
    )

    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        mock_alarm_control_panel_entities["no_arm_code"].unique_id,
        device_id=device_entry.id,
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
                            "event_type": "test_event_arm_away",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entity_entry.entity_id,
                            "type": "arm_away",
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    expect(
        await async_setup_component(hass, DOMAIN, {DOMAIN: {CONF_PLATFORM: "test"}})
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(hass.states.get(entity_entry.entity_id).state).to_equal(STATE_UNKNOWN)

    hass.bus.async_fire("test_event_arm_away")
    await hass.async_block_till_done()
    expect(hass.states.get(entity_entry.entity_id).state).to_equal(
        AlarmControlPanelState.ARMED_AWAY
    )
