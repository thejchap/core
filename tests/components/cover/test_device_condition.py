"""The tests for Cover device conditions (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.cover import DOMAIN, CoverEntityFeature, CoverState
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.const import CONF_PLATFORM, STATE_UNAVAILABLE, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryHider
from homeassistant.setup import async_setup_component

from ._fixtures import mock_cover_entities as mock_cover_entities_fixture
from .common import MockCover

from tests.common import (
    MockConfigEntry,
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
        "no_features",
        set_state=False,
        features_reg=0,
        features_state=0,
        expected_condition_types=[],
    ),
    test.case(
        "close",
        set_state=False,
        features_reg=CoverEntityFeature.CLOSE,
        features_state=0,
        expected_condition_types=["is_open", "is_closed", "is_opening", "is_closing"],
    ),
    test.case(
        "open",
        set_state=False,
        features_reg=CoverEntityFeature.OPEN,
        features_state=0,
        expected_condition_types=["is_open", "is_closed", "is_opening", "is_closing"],
    ),
    test.case(
        "set_position",
        set_state=False,
        features_reg=CoverEntityFeature.SET_POSITION,
        features_state=0,
        expected_condition_types=["is_position"],
    ),
    test.case(
        "set_tilt_position",
        set_state=False,
        features_reg=CoverEntityFeature.SET_TILT_POSITION,
        features_state=0,
        expected_condition_types=["is_tilt_position"],
    ),
    test.case(
        "set_no_features",
        set_state=True,
        features_reg=0,
        features_state=0,
        expected_condition_types=[],
    ),
    test.case(
        "set_close",
        set_state=True,
        features_reg=0,
        features_state=CoverEntityFeature.CLOSE,
        expected_condition_types=["is_open", "is_closed", "is_opening", "is_closing"],
    ),
    test.case(
        "set_open",
        set_state=True,
        features_reg=0,
        features_state=CoverEntityFeature.OPEN,
        expected_condition_types=["is_open", "is_closed", "is_opening", "is_closing"],
    ),
    test.case(
        "set_set_position",
        set_state=True,
        features_reg=0,
        features_state=CoverEntityFeature.SET_POSITION,
        expected_condition_types=["is_position"],
    ),
    test.case(
        "set_set_tilt_position",
        set_state=True,
        features_reg=0,
        features_state=CoverEntityFeature.SET_TILT_POSITION,
        expected_condition_types=["is_tilt_position"],
    ),
)
async def get_conditions(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    set_state: bool,
    features_reg: int,
    features_state: int,
    expected_condition_types: list[str],
) -> None:
    """Test we get the expected conditions from a cover."""
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
    await hass.async_block_till_done()

    expected_conditions = [
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
        supported_features=CoverEntityFeature.CLOSE,
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
        for condition in ("is_open", "is_closed", "is_opening", "is_closing")
    ]
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(conditions).to_equal(unordered(expected_conditions))


@test
async def get_condition_capabilities(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test we get the expected capabilities from a cover condition."""
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

    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(len(conditions)).to_equal(4)
    for condition in conditions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.CONDITION, condition
        )
        expect(capabilities).to_equal({"extra_fields": []})


@test
async def get_condition_capabilities_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test we get the expected capabilities from a cover condition."""
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

    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(len(conditions)).to_equal(4)
    for condition in conditions:
        condition["entity_id"] = entity_registry.async_get(
            condition["entity_id"]
        ).entity_id
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.CONDITION, condition
        )
        expect(capabilities).to_equal({"extra_fields": []})


@test
async def get_condition_capabilities_set_pos(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test we get the expected capabilities from a cover condition."""
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
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(len(conditions)).to_equal(5)
    for condition in conditions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.CONDITION, condition
        )
        if condition["type"] == "is_position":
            expect(capabilities).to_equal(expected_capabilities)
        else:
            expect(capabilities).to_equal({"extra_fields": []})


@test
async def get_condition_capabilities_set_tilt_pos(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test we get the expected capabilities from a cover condition."""
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
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(len(conditions)).to_equal(5)
    for condition in conditions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.CONDITION, condition
        )
        if condition["type"] == "is_tilt_position":
            expect(capabilities).to_equal(expected_capabilities)
        else:
            expect(capabilities).to_equal({"extra_fields": []})


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

    hass.states.async_set(entry.entity_id, CoverState.OPEN)

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
                                "type": "is_open",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_open "
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
                                "type": "is_closed",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_closed "
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
                                "type": "is_opening",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_opening "
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
                                "type": "is_closing",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_closing "
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
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("is_open - event - test_event1")

    hass.states.async_set(entry.entity_id, CoverState.CLOSED)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal("is_closed - event - test_event2")

    hass.states.async_set(entry.entity_id, CoverState.OPENING)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect(service_calls[2].data["some"]).to_equal("is_opening - event - test_event3")

    hass.states.async_set(entry.entity_id, CoverState.CLOSING)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event4")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(4)
    expect(service_calls[3].data["some"]).to_equal("is_closing - event - test_event4")


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

    hass.states.async_set(entry.entity_id, CoverState.OPEN)

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
                                "type": "is_open",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_open "
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
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("is_open - event - test_event1")


@test
async def if_position(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test for position conditions."""
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
                        "trigger": {"platform": "event", "event_type": "test_event1"},
                        "action": {
                            "choose": {
                                "conditions": {
                                    "condition": "device",
                                    "domain": DOMAIN,
                                    "device_id": device_entry.id,
                                    "entity_id": entry.id,
                                    "type": "is_position",
                                    "above": 45,
                                },
                                "sequence": {
                                    "service": "test.automation",
                                    "data_template": {
                                        "some": (
                                            "is_pos_gt_45 "
                                            "- {{ trigger.platform }} "
                                            "- {{ trigger.event.event_type }}"
                                        )
                                    },
                                },
                            },
                            "default": {
                                "service": "test.automation",
                                "data_template": {
                                    "some": (
                                        "is_pos_not_gt_45 "
                                        "- {{ trigger.platform }} "
                                        "- {{ trigger.event.event_type }}"
                                    )
                                },
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
                                "type": "is_position",
                                "below": 90,
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_pos_lt_90 "
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
                                "type": "is_position",
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
                                    "- {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect(service_calls[0].data["some"]).to_equal(
        "is_pos_gt_45 - event - test_event1"
    )
    expect(service_calls[1].data["some"]).to_equal(
        "is_pos_lt_90 - event - test_event2"
    )
    expect(service_calls[2].data["some"]).to_equal(
        "is_pos_gt_45_lt_90 - event - test_event3"
    )

    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_position": 45}
    )
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(5)
    expect(service_calls[3].data["some"]).to_equal(
        "is_pos_not_gt_45 - event - test_event1"
    )
    expect(service_calls[4].data["some"]).to_equal(
        "is_pos_lt_90 - event - test_event2"
    )

    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_position": 90}
    )
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(6)
    expect(service_calls[5].data["some"]).to_equal(
        "is_pos_gt_45 - event - test_event1"
    )

    hass.states.async_set(ent.entity_id, STATE_UNAVAILABLE, attributes={})
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(7)
    expect(service_calls[6].data["some"]).to_equal(
        "is_pos_not_gt_45 - event - test_event1"
    )


@test
async def if_tilt_position(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test for tilt position conditions."""
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
                        "trigger": {"platform": "event", "event_type": "test_event1"},
                        "action": {
                            "choose": {
                                "conditions": {
                                    "condition": "device",
                                    "domain": DOMAIN,
                                    "device_id": device_entry.id,
                                    "entity_id": entry.id,
                                    "type": "is_tilt_position",
                                    "above": 45,
                                },
                                "sequence": {
                                    "service": "test.automation",
                                    "data_template": {
                                        "some": (
                                            "is_pos_gt_45 "
                                            "- {{ trigger.platform }} "
                                            "- {{ trigger.event.event_type }}"
                                        )
                                    },
                                },
                            },
                            "default": {
                                "service": "test.automation",
                                "data_template": {
                                    "some": (
                                        "is_pos_not_gt_45 "
                                        "- {{ trigger.platform }} "
                                        "- {{ trigger.event.event_type }}"
                                    )
                                },
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
                                "type": "is_tilt_position",
                                "below": 90,
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_pos_lt_90 "
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
                                "type": "is_tilt_position",
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
                                    "- {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect(service_calls[0].data["some"]).to_equal(
        "is_pos_gt_45 - event - test_event1"
    )
    expect(service_calls[1].data["some"]).to_equal(
        "is_pos_lt_90 - event - test_event2"
    )
    expect(service_calls[2].data["some"]).to_equal(
        "is_pos_gt_45_lt_90 - event - test_event3"
    )

    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_tilt_position": 45}
    )
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(5)
    expect(service_calls[3].data["some"]).to_equal(
        "is_pos_not_gt_45 - event - test_event1"
    )
    expect(service_calls[4].data["some"]).to_equal(
        "is_pos_lt_90 - event - test_event2"
    )

    hass.states.async_set(
        ent.entity_id, CoverState.CLOSED, attributes={"current_tilt_position": 90}
    )
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(6)
    expect(service_calls[5].data["some"]).to_equal(
        "is_pos_gt_45 - event - test_event1"
    )

    hass.states.async_set(ent.entity_id, STATE_UNAVAILABLE, attributes={})
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(7)
    expect(service_calls[6].data["some"]).to_equal(
        "is_pos_not_gt_45 - event - test_event1"
    )
