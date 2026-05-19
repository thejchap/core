"""The tests for Alarm control panel device conditions (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.alarm_control_panel import (
    DOMAIN,
    AlarmControlPanelEntityFeature,
    AlarmControlPanelState,
)
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.setup import async_setup_component

from ._fixtures import service_calls as service_calls_fixture

from tests.common import MockConfigEntry, async_get_device_automations
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


@test.cases(
    test.case(
        "noset_none",
        set_state=False,
        features_reg=0,
        features_state=0,
        expected_condition_types=[],
    ),
    test.case(
        "noset_arm_away",
        set_state=False,
        features_reg=AlarmControlPanelEntityFeature.ARM_AWAY,
        features_state=0,
        expected_condition_types=["is_armed_away"],
    ),
    test.case(
        "noset_arm_home",
        set_state=False,
        features_reg=AlarmControlPanelEntityFeature.ARM_HOME,
        features_state=0,
        expected_condition_types=["is_armed_home"],
    ),
    test.case(
        "noset_arm_night",
        set_state=False,
        features_reg=AlarmControlPanelEntityFeature.ARM_NIGHT,
        features_state=0,
        expected_condition_types=["is_armed_night"],
    ),
    test.case(
        "noset_arm_vacation",
        set_state=False,
        features_reg=AlarmControlPanelEntityFeature.ARM_VACATION,
        features_state=0,
        expected_condition_types=["is_armed_vacation"],
    ),
    test.case(
        "noset_arm_custom_bypass",
        set_state=False,
        features_reg=AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS,
        features_state=0,
        expected_condition_types=["is_armed_custom_bypass"],
    ),
    test.case(
        "set_none",
        set_state=True,
        features_reg=0,
        features_state=0,
        expected_condition_types=[],
    ),
    test.case(
        "set_arm_away",
        set_state=True,
        features_reg=0,
        features_state=AlarmControlPanelEntityFeature.ARM_AWAY,
        expected_condition_types=["is_armed_away"],
    ),
    test.case(
        "set_arm_home",
        set_state=True,
        features_reg=0,
        features_state=AlarmControlPanelEntityFeature.ARM_HOME,
        expected_condition_types=["is_armed_home"],
    ),
    test.case(
        "set_arm_night",
        set_state=True,
        features_reg=0,
        features_state=AlarmControlPanelEntityFeature.ARM_NIGHT,
        expected_condition_types=["is_armed_night"],
    ),
    test.case(
        "set_arm_vacation",
        set_state=True,
        features_reg=0,
        features_state=AlarmControlPanelEntityFeature.ARM_VACATION,
        expected_condition_types=["is_armed_vacation"],
    ),
    test.case(
        "set_arm_custom_bypass",
        set_state=True,
        features_reg=0,
        features_state=AlarmControlPanelEntityFeature.ARM_CUSTOM_BYPASS,
        expected_condition_types=["is_armed_custom_bypass"],
    ),
)
async def get_conditions(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    set_state: bool,
    features_reg: int,
    features_state: int,
    expected_condition_types: list[str],
) -> None:
    """Test we get the expected conditions from a alarm_control_panel."""
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
            "alarm_control_panel.test_5678",
            "attributes",
            {"supported_features": features_state},
        )
    basic_condition_types = ["is_disarmed", "is_triggered"]
    expected_conditions = [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": condition,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
        for condition in basic_condition_types
    ]
    expected_conditions += [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": condition,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
        for condition in expected_condition_types
    ]
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(conditions).to_equal(unordered(expected_conditions))


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
async def get_conditions_hidden_auxiliary(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    hidden_by: er.RegistryEntryHider | None,
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
        for condition in ("is_disarmed", "is_triggered")
    ]
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(conditions).to_equal(unordered(expected_conditions))


@test
async def if_state(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test for all conditions."""
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
                                "type": "is_triggered",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_triggered "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.event.event_type }}"
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
                                "type": "is_disarmed",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_disarmed "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                    {
                        "trigger": {"platform": "event", "event_type": "test_event3"},
                        "condition": [
                            {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "is_armed_home",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_armed_home "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                    {
                        "trigger": {"platform": "event", "event_type": "test_event4"},
                        "condition": [
                            {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "is_armed_away",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_armed_away "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                    {
                        "trigger": {"platform": "event", "event_type": "test_event5"},
                        "condition": [
                            {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "is_armed_night",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_armed_night "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                    {
                        "trigger": {"platform": "event", "event_type": "test_event6"},
                        "condition": [
                            {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "is_armed_vacation",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_armed_vacation "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                    {
                        "trigger": {"platform": "event", "event_type": "test_event7"},
                        "condition": [
                            {
                                "condition": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "is_armed_custom_bypass",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_armed_custom_bypass "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    hass.states.async_set(entry.entity_id, AlarmControlPanelState.TRIGGERED)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("is_triggered - event - test_event1")

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.DISARMED)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal("is_disarmed - event - test_event2")

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_HOME)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect(service_calls[2].data["some"]).to_equal("is_armed_home - event - test_event3")

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_AWAY)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(4)
    expect(service_calls[3].data["some"]).to_equal("is_armed_away - event - test_event4")

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_NIGHT)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(5)
    expect(service_calls[4].data["some"]).to_equal(
        "is_armed_night - event - test_event5"
    )

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_VACATION)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(6)
    expect(service_calls[5].data["some"]).to_equal(
        "is_armed_vacation - event - test_event6"
    )

    hass.states.async_set(entry.entity_id, AlarmControlPanelState.ARMED_CUSTOM_BYPASS)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    hass.bus.async_fire("test_event4")
    hass.bus.async_fire("test_event5")
    hass.bus.async_fire("test_event6")
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(7)
    expect(service_calls[6].data["some"]).to_equal(
        "is_armed_custom_bypass - event - test_event7"
    )


@test
async def if_state_legacy(
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test for all conditions."""
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
                                "entity_id": entry.entity_id,
                                "type": "is_triggered",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_triggered "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    hass.states.async_set(entry.entity_id, AlarmControlPanelState.TRIGGERED)
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("is_triggered - event - test_event1")
