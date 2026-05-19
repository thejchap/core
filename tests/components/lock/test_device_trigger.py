"""The tests for Lock device triggers (tryke port)."""

from datetime import timedelta

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.lock import DOMAIN, LockEntityFeature, LockState
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryHider
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_get_device_automation_capabilities,
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
    """Test we get the expected triggers from a lock."""
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
        supported_features=LockEntityFeature.OPEN,
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
        for trigger in (
            "locked",
            "unlocked",
            "unlocking",
            "locking",
            "jammed",
            "open",
            "opening",
        )
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
        supported_features=LockEntityFeature.OPEN,
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
        for trigger in (
            "locked",
            "unlocked",
            "unlocking",
            "locking",
            "jammed",
            "open",
            "opening",
        )
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
    """Test we get the expected capabilities from a lock."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(len(triggers)).to_equal(7)
    for trigger in triggers:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.TRIGGER, trigger
        )
        expect(capabilities).to_equal(
            {
                "extra_fields": [
                    {
                        "name": "for",
                        "optional": True,
                        "required": False,
                        "type": "positive_time_period_dict",
                    }
                ]
            }
        )


@test
async def get_trigger_capabilities_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a lock."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(len(triggers)).to_equal(7)
    for trigger in triggers:
        trigger["entity_id"] = entity_registry.async_get(trigger["entity_id"]).entity_id
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.TRIGGER, trigger
        )
        expect(capabilities).to_equal(
            {
                "extra_fields": [
                    {
                        "name": "for",
                        "optional": True,
                        "required": False,
                        "type": "positive_time_period_dict",
                    }
                ]
            }
        )


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

    hass.states.async_set(entry.entity_id, LockState.UNLOCKED)

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
                            "type": "locked",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "locked - {{ trigger.platform}} - "
                                    "{{ trigger.entity_id}} - {{ trigger.from_state.state}} - "
                                    "{{ trigger.to_state.state}} - {{ trigger.for }}"
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
                            "type": "unlocked",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "unlocked - {{ trigger.platform}} - "
                                    "{{ trigger.entity_id}} - {{ trigger.from_state.state}} - "
                                    "{{ trigger.to_state.state}} - {{ trigger.for }}"
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
                            "type": "open",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "open - {{ trigger.platform}} - "
                                    "{{ trigger.entity_id}} - {{ trigger.from_state.state}} - "
                                    "{{ trigger.to_state.state}} - {{ trigger.for }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    hass.states.async_set(entry.entity_id, LockState.LOCKED)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"locked - device - {entry.entity_id} - unlocked - locked - None"
    )

    hass.states.async_set(entry.entity_id, LockState.UNLOCKED)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal(
        f"unlocked - device - {entry.entity_id} - locked - unlocked - None"
    )

    hass.states.async_set(entry.entity_id, LockState.OPEN)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect(service_calls[2].data["some"]).to_equal(
        f"open - device - {entry.entity_id} - unlocked - open - None"
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

    hass.states.async_set(entry.entity_id, LockState.UNLOCKED)

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
                            "type": "locked",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "locked - {{ trigger.platform}} - "
                                    "{{ trigger.entity_id}} - {{ trigger.from_state.state}} - "
                                    "{{ trigger.to_state.state}} - {{ trigger.for }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    hass.states.async_set(entry.entity_id, LockState.LOCKED)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"locked - device - {entry.entity_id} - unlocked - locked - None"
    )


@test
async def if_fires_on_state_change_with_for(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
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

    hass.states.async_set(entry.entity_id, LockState.UNLOCKED)

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
                            "type": "locked",
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
                    },
                    {
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "unlocking",
                            "for": {"seconds": 5},
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "turn_on {{ trigger.platform }}"
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
                            "type": "jammed",
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
                    },
                    {
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "locking",
                            "for": {"seconds": 5},
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "turn_on {{ trigger.platform }}"
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
                            "type": "opening",
                            "for": {"seconds": 5},
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "turn_on {{ trigger.platform }}"
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
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, LockState.LOCKED)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    await hass.async_block_till_done()
    expect(service_calls[0].data["some"]).to_equal(
        f"turn_off device - {entry.entity_id} - unlocked - locked - 0:00:05"
    )

    hass.states.async_set(entry.entity_id, LockState.UNLOCKING)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=16))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    await hass.async_block_till_done()
    expect(service_calls[1].data["some"]).to_equal(
        f"turn_on device - {entry.entity_id} - locked - unlocking - 0:00:05"
    )

    hass.states.async_set(entry.entity_id, LockState.JAMMED)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=21))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    await hass.async_block_till_done()
    expect(service_calls[2].data["some"]).to_equal(
        f"turn_off device - {entry.entity_id} - unlocking - jammed - 0:00:05"
    )

    hass.states.async_set(entry.entity_id, LockState.LOCKING)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=27))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(4)
    await hass.async_block_till_done()
    expect(service_calls[3].data["some"]).to_equal(
        f"turn_on device - {entry.entity_id} - jammed - locking - 0:00:05"
    )

    hass.states.async_set(entry.entity_id, LockState.OPENING)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(4)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=27))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(5)
    await hass.async_block_till_done()
    expect(service_calls[4].data["some"]).to_equal(
        f"turn_on device - {entry.entity_id} - locking - opening - 0:00:05"
    )
