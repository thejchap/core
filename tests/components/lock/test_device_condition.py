"""The tests for Lock device conditions (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.lock import DOMAIN, LockState
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
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
async def get_conditions(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected conditions from a lock."""
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
            "type": condition,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
        for condition in (
            "is_locked",
            "is_unlocked",
            "is_unlocking",
            "is_locking",
            "is_jammed",
            "is_open",
            "is_opening",
        )
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
    hass: HomeAssistant = Depends(_trigger_executor),
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
        for condition in (
            "is_locked",
            "is_unlocked",
            "is_unlocking",
            "is_locking",
            "is_jammed",
            "is_open",
            "is_opening",
        )
    ]
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(conditions).to_equal(unordered(expected_conditions))


@test
async def if_state(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for turn_on and turn_off conditions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, LockState.LOCKED)

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
                                "type": "is_locked",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": "is_locked - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                                "type": "is_unlocked",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": "is_unlocked - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                                "type": "is_unlocking",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": "is_unlocking - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                                "type": "is_locking",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": "is_locking - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                                "type": "is_jammed",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": "is_jammed - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                                "type": "is_opening",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": "is_opening - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
                                "type": "is_open",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": "is_open - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("is_locked - event - test_event1")

    hass.states.async_set(entry.entity_id, LockState.UNLOCKED)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal("is_unlocked - event - test_event2")

    hass.states.async_set(entry.entity_id, LockState.UNLOCKING)
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect(service_calls[2].data["some"]).to_equal(
        "is_unlocking - event - test_event3"
    )

    hass.states.async_set(entry.entity_id, LockState.LOCKING)
    hass.bus.async_fire("test_event4")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(4)
    expect(service_calls[3].data["some"]).to_equal("is_locking - event - test_event4")

    hass.states.async_set(entry.entity_id, LockState.JAMMED)
    hass.bus.async_fire("test_event5")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(5)
    expect(service_calls[4].data["some"]).to_equal("is_jammed - event - test_event5")

    hass.states.async_set(entry.entity_id, LockState.OPENING)
    hass.bus.async_fire("test_event6")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(6)
    expect(service_calls[5].data["some"]).to_equal("is_opening - event - test_event6")

    hass.states.async_set(entry.entity_id, LockState.OPEN)
    hass.bus.async_fire("test_event7")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(7)
    expect(service_calls[6].data["some"]).to_equal("is_open - event - test_event7")


@test
async def if_state_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for turn_on and turn_off conditions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, LockState.LOCKED)

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
                                "type": "is_locked",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": "is_locked - {{ trigger.platform }} - {{ trigger.event.event_type }}"
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
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("is_locked - event - test_event1")
