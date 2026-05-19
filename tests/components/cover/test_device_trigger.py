"""The tests for Cover device triggers (tryke port)."""

from datetime import timedelta

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.cover import DOMAIN, CoverEntityFeature, CoverState
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.const import CONF_PLATFORM, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryHider
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from ._fixtures import mock_cover_entities as mock_cover_entities_fixture
from .common import MockCover

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


@test.cases(
    test.case(
        "open",
        set_state=False,
        features_reg=CoverEntityFeature.OPEN,
        features_state=0,
        expected_trigger_types=["opened", "closed", "opening", "closing"],
    ),
    test.case(
        "open_set_position",
        set_state=False,
        features_reg=CoverEntityFeature.OPEN | CoverEntityFeature.SET_POSITION,
        features_state=0,
        expected_trigger_types=["opened", "closed", "opening", "closing", "position"],
    ),
    test.case(
        "open_set_tilt_position",
        set_state=False,
        features_reg=CoverEntityFeature.OPEN | CoverEntityFeature.SET_TILT_POSITION,
        features_state=0,
        expected_trigger_types=[
            "opened",
            "closed",
            "opening",
            "closing",
            "tilt_position",
        ],
    ),
    test.case(
        "set_open",
        set_state=True,
        features_reg=0,
        features_state=CoverEntityFeature.OPEN,
        expected_trigger_types=["opened", "closed", "opening", "closing"],
    ),
    test.case(
        "set_open_set_position",
        set_state=True,
        features_reg=0,
        features_state=CoverEntityFeature.OPEN | CoverEntityFeature.SET_POSITION,
        expected_trigger_types=["opened", "closed", "opening", "closing", "position"],
    ),
    test.case(
        "set_open_set_tilt_position",
        set_state=True,
        features_reg=0,
        features_state=CoverEntityFeature.OPEN | CoverEntityFeature.SET_TILT_POSITION,
        expected_trigger_types=[
            "opened",
            "closed",
            "opening",
            "closing",
            "tilt_position",
        ],
    ),
)
async def get_triggers(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    set_state: bool,
    features_reg: int,
    features_state: int,
    expected_trigger_types: list[str],
) -> None:
    """Test we get the expected triggers from a cover."""
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
            entity_entry.entity_id,
            "attributes",
            {"supported_features": features_state},
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
        for trigger in expected_trigger_types
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
        supported_features=CoverEntityFeature.OPEN,
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
        for trigger in ("opened", "closed", "opening", "closing")
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
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test we get the expected capabilities from a cover trigger."""
    setup_test_component_platform(hass, DOMAIN, mock_cover_entities)
    ent = mock_cover_entities[0]
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
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(len(triggers)).to_equal(4)
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
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test we get the expected capabilities from a cover trigger."""
    setup_test_component_platform(hass, DOMAIN, mock_cover_entities)
    ent = mock_cover_entities[0]
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
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(len(triggers)).to_equal(4)
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
async def get_trigger_capabilities_set_pos(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test we get the expected capabilities from a cover trigger."""
    setup_test_component_platform(hass, DOMAIN, mock_cover_entities)
    ent = mock_cover_entities[1]
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
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )

    expected_capabilities = {
        "extra_fields": [
            {
                "name": "above",
                "optional": True,
                "required": False,
                "type": "integer",
                "default": 0,
                "valueMax": 100,
                "valueMin": 0,
            },
            {
                "name": "below",
                "optional": True,
                "required": False,
                "type": "integer",
                "default": 100,
                "valueMax": 100,
                "valueMin": 0,
            },
        ]
    }
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(len(triggers)).to_equal(5)
    for trigger in triggers:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.TRIGGER, trigger
        )
        if trigger["type"] == "position":
            expect(capabilities).to_equal(expected_capabilities)
        else:
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
async def get_trigger_capabilities_set_tilt_pos(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test we get the expected capabilities from a cover trigger."""
    setup_test_component_platform(hass, DOMAIN, mock_cover_entities)
    ent = mock_cover_entities[3]
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
        DOMAIN, "test", ent.unique_id, device_id=device_entry.id
    )

    expected_capabilities = {
        "extra_fields": [
            {
                "name": "above",
                "optional": True,
                "required": False,
                "type": "integer",
                "default": 0,
                "valueMax": 100,
                "valueMin": 0,
            },
            {
                "name": "below",
                "optional": True,
                "required": False,
                "type": "integer",
                "default": 100,
                "valueMax": 100,
                "valueMin": 0,
            },
        ]
    }
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(len(triggers)).to_equal(5)
    for trigger in triggers:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.TRIGGER, trigger
        )
        if trigger["type"] == "tilt_position":
            expect(capabilities).to_equal(expected_capabilities)
        else:
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
    """Test for state triggers firing."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, CoverState.CLOSED)

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
                            "type": "opened",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "opened "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.entity_id }} "
                                    "- {{ trigger.from_state.state }} "
                                    "- {{ trigger.to_state.state }} "
                                    "- {{ trigger.for }}"
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
                            "type": "closed",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "closed "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.entity_id }} "
                                    "- {{ trigger.from_state.state }} "
                                    "- {{ trigger.to_state.state }} "
                                    "- {{ trigger.for }}"
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
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "opening "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.entity_id }} "
                                    "- {{ trigger.from_state.state }} "
                                    "- {{ trigger.to_state.state }} "
                                    "- {{ trigger.for }}"
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
                            "type": "closing",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "closing "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.entity_id }} "
                                    "- {{ trigger.from_state.state }} "
                                    "- {{ trigger.to_state.state }} "
                                    "- {{ trigger.for }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    hass.states.async_set(entry.entity_id, CoverState.OPEN)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"opened - device - {entry.entity_id} - closed - open - None"
    )

    hass.states.async_set(entry.entity_id, CoverState.CLOSED)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal(
        f"closed - device - {entry.entity_id} - open - closed - None"
    )

    hass.states.async_set(entry.entity_id, CoverState.OPENING)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect(service_calls[2].data["some"]).to_equal(
        f"opening - device - {entry.entity_id} - closed - opening - None"
    )

    hass.states.async_set(entry.entity_id, CoverState.CLOSING)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(4)
    expect(service_calls[3].data["some"]).to_equal(
        f"closing - device - {entry.entity_id} - opening - closing - None"
    )


@test
async def if_fires_on_state_change_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for state triggers firing."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(entry.entity_id, CoverState.CLOSED)

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
                            "type": "opened",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "opened "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.entity_id }} "
                                    "- {{ trigger.from_state.state }} "
                                    "- {{ trigger.to_state.state }} "
                                    "- {{ trigger.for }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    hass.states.async_set(entry.entity_id, CoverState.OPEN)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        f"opened - device - {entry.entity_id} - closed - open - None"
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

    hass.states.async_set(entry.entity_id, CoverState.CLOSED)

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
                            "type": "opened",
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
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, CoverState.OPEN)
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=10))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    await hass.async_block_till_done()
    expect(service_calls[0].data["some"]).to_equal(
        f"turn_off device - {entry.entity_id} - closed - open - 0:00:05"
    )


@test
async def if_fires_on_position(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test for position triggers."""
    setup_test_component_platform(hass, DOMAIN, mock_cover_entities)
    ent = mock_cover_entities[1]
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
    entry = entity_registry.async_get(ent.entity_id)
    entity_registry.async_update_entity(entry.entity_id, device_id=device_entry.id)

    service_calls = async_mock_service(hass, "test", "automation")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": [
                            {
                                "platform": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "position",
                                "above": 45,
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_pos_gt_45 "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.entity_id }} "
                                    "- {{ trigger.from_state.state }} "
                                    "- {{ trigger.to_state.state }} "
                                    "- {{ trigger.for }}"
                                )
                            },
                        },
                    },
                    {
                        "trigger": [
                            {
                                "platform": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "position",
                                "below": 90,
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_pos_lt_90 "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.entity_id }} "
                                    "- {{ trigger.from_state.state }} "
                                    "- {{ trigger.to_state.state }} "
                                    "- {{ trigger.for }}"
                                )
                            },
                        },
                    },
                    {
                        "trigger": [
                            {
                                "platform": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "position",
                                "above": 45,
                                "below": 90,
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_pos_gt_45_lt_90 "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.entity_id }} "
                                    "- {{ trigger.from_state.state }} "
                                    "- {{ trigger.to_state.state }} "
                                    "- {{ trigger.for }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    hass.states.async_set(
        ent.entity_id, CoverState.OPEN, attributes={"current_position": 1}
    )
    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_position": 95}
    )
    hass.states.async_set(
        ent.entity_id, CoverState.OPEN, attributes={"current_position": 50}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect(
        sorted(
            [
                service_calls[0].data["some"],
                service_calls[1].data["some"],
                service_calls[2].data["some"],
            ]
        )
    ).to_equal(
        sorted(
            [
                f"is_pos_gt_45_lt_90 - device - {entry.entity_id} - closed - open - None",
                f"is_pos_lt_90 - device - {entry.entity_id} - closed - open - None",
                f"is_pos_gt_45 - device - {entry.entity_id} - open - closed - None",
            ]
        )
    )

    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_position": 95}
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_position": 45}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(4)
    expect(service_calls[3].data["some"]).to_equal(
        f"is_pos_lt_90 - device - {entry.entity_id} - closed - closed - None"
    )

    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_position": 90}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(5)
    expect(service_calls[4].data["some"]).to_equal(
        f"is_pos_gt_45 - device - {entry.entity_id} - closed - closed - None"
    )


@test
async def if_fires_on_tilt_position(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test for tilt position triggers."""
    setup_test_component_platform(hass, DOMAIN, mock_cover_entities)
    ent = mock_cover_entities[1]
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
    entry = entity_registry.async_get(ent.entity_id)
    entity_registry.async_update_entity(entry.entity_id, device_id=device_entry.id)

    service_calls = async_mock_service(hass, "test", "automation")

    expect(
        await async_setup_component(
            hass,
            automation.DOMAIN,
            {
                automation.DOMAIN: [
                    {
                        "trigger": [
                            {
                                "platform": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "tilt_position",
                                "above": 45,
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_pos_gt_45 "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.entity_id }} "
                                    "- {{ trigger.from_state.state }} "
                                    "- {{ trigger.to_state.state }} "
                                    "- {{ trigger.for }}"
                                )
                            },
                        },
                    },
                    {
                        "trigger": [
                            {
                                "platform": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "tilt_position",
                                "below": 90,
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_pos_lt_90 "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.entity_id }} "
                                    "- {{ trigger.from_state.state }} "
                                    "- {{ trigger.to_state.state }} "
                                    "- {{ trigger.for }}"
                                )
                            },
                        },
                    },
                    {
                        "trigger": [
                            {
                                "platform": "device",
                                "domain": DOMAIN,
                                "device_id": device_entry.id,
                                "entity_id": entry.id,
                                "type": "tilt_position",
                                "above": 45,
                                "below": 90,
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_pos_gt_45_lt_90 "
                                    "- {{ trigger.platform }} "
                                    "- {{ trigger.entity_id }} "
                                    "- {{ trigger.from_state.state }} "
                                    "- {{ trigger.to_state.state }} "
                                    "- {{ trigger.for }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    hass.states.async_set(
        ent.entity_id, CoverState.OPEN, attributes={"current_tilt_position": 1}
    )
    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_tilt_position": 95}
    )
    hass.states.async_set(
        ent.entity_id, CoverState.OPEN, attributes={"current_tilt_position": 50}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect(
        sorted(
            [
                service_calls[0].data["some"],
                service_calls[1].data["some"],
                service_calls[2].data["some"],
            ]
        )
    ).to_equal(
        sorted(
            [
                f"is_pos_gt_45_lt_90 - device - {entry.entity_id} - closed - open - None",
                f"is_pos_lt_90 - device - {entry.entity_id} - closed - open - None",
                f"is_pos_gt_45 - device - {entry.entity_id} - open - closed - None",
            ]
        )
    )

    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_tilt_position": 95}
    )
    await hass.async_block_till_done()
    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_tilt_position": 45}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(4)
    expect(service_calls[3].data["some"]).to_equal(
        f"is_pos_lt_90 - device - {entry.entity_id} - closed - closed - None"
    )

    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_tilt_position": 90}
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(5)
    expect(service_calls[4].data["some"]).to_equal(
        f"is_pos_gt_45 - device - {entry.entity_id} - closed - closed - None"
    )
