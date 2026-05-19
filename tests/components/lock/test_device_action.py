"""The tests for Lock device actions (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.lock import DOMAIN, LockEntityFeature
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


@test.cases(
    test.case(
        "noset_none",
        set_state=False,
        features_reg=0,
        features_state=0,
        expected_action_types=[],
    ),
    test.case(
        "noset_open",
        set_state=False,
        features_reg=LockEntityFeature.OPEN,
        features_state=0,
        expected_action_types=["open"],
    ),
    test.case(
        "set_none",
        set_state=True,
        features_reg=0,
        features_state=0,
        expected_action_types=[],
    ),
    test.case(
        "set_open",
        set_state=True,
        features_reg=0,
        features_state=LockEntityFeature.OPEN,
        expected_action_types=["open"],
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
    """Test we get the expected actions from a lock."""
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
            f"{DOMAIN}.test_5678",
            "attributes",
            {"supported_features": features_state},
        )
    basic_action_types = ["lock", "unlock"]
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": action,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
        for action in basic_action_types
    ]
    expected_actions += [
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
        "integration", hidden_by=RegistryEntryHider.INTEGRATION, entity_category=None
    ),
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
        supported_features=0,
    )
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": action,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": True},
        }
        for action in ("lock", "unlock")
    ]
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(actions).to_equal(unordered(expected_actions))


@test
async def action(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for lock actions."""
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
                            "event_type": "test_event_lock",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "lock",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_unlock",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "unlock",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_open",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "open",
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    lock_calls = async_mock_service(hass, "lock", "lock")
    unlock_calls = async_mock_service(hass, "lock", "unlock")
    open_calls = async_mock_service(hass, "lock", "open")

    hass.bus.async_fire("test_event_lock")
    await hass.async_block_till_done()
    expect(len(lock_calls)).to_equal(1)
    expect(len(unlock_calls)).to_equal(0)
    expect(len(open_calls)).to_equal(0)

    hass.bus.async_fire("test_event_unlock")
    await hass.async_block_till_done()
    expect(len(lock_calls)).to_equal(1)
    expect(len(unlock_calls)).to_equal(1)
    expect(len(open_calls)).to_equal(0)

    hass.bus.async_fire("test_event_open")
    await hass.async_block_till_done()
    expect(len(lock_calls)).to_equal(1)
    expect(len(unlock_calls)).to_equal(1)
    expect(len(open_calls)).to_equal(1)

    expect(lock_calls[0].domain).to_equal(DOMAIN)
    expect(lock_calls[0].service).to_equal("lock")
    expect(lock_calls[0].data).to_equal({"entity_id": entry.entity_id})
    expect(unlock_calls[0].domain).to_equal(DOMAIN)
    expect(unlock_calls[0].service).to_equal("unlock")
    expect(unlock_calls[0].data).to_equal({"entity_id": entry.entity_id})
    expect(open_calls[0].domain).to_equal(DOMAIN)
    expect(open_calls[0].service).to_equal("open")
    expect(open_calls[0].data).to_equal({"entity_id": entry.entity_id})


@test
async def action_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for lock actions."""
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
                            "event_type": "test_event_lock",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "lock",
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    lock_calls = async_mock_service(hass, "lock", "lock")

    hass.bus.async_fire("test_event_lock")
    await hass.async_block_till_done()
    expect(len(lock_calls)).to_equal(1)

    expect(lock_calls[0].domain).to_equal(DOMAIN)
    expect(lock_calls[0].service).to_equal("lock")
    expect(lock_calls[0].data).to_equal({"entity_id": entry.entity_id})
