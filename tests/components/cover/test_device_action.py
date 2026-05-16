"""The tests for Cover device actions (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components import automation
from homeassistant.components.cover import DOMAIN, CoverEntityFeature
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.const import CONF_PLATFORM, EntityCategory
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
    test.case("noset_none", set_state=False, features_reg=0, features_state=0, expected_action_types=[]),
    test.case("noset_close_tilt", set_state=False, features_reg=CoverEntityFeature.CLOSE_TILT, features_state=0, expected_action_types=["close_tilt"]),
    test.case("noset_close", set_state=False, features_reg=CoverEntityFeature.CLOSE, features_state=0, expected_action_types=["close"]),
    test.case("noset_open_tilt", set_state=False, features_reg=CoverEntityFeature.OPEN_TILT, features_state=0, expected_action_types=["open_tilt"]),
    test.case("noset_open", set_state=False, features_reg=CoverEntityFeature.OPEN, features_state=0, expected_action_types=["open"]),
    test.case("noset_set_position", set_state=False, features_reg=CoverEntityFeature.SET_POSITION, features_state=0, expected_action_types=["set_position"]),
    test.case("noset_set_tilt_position", set_state=False, features_reg=CoverEntityFeature.SET_TILT_POSITION, features_state=0, expected_action_types=["set_tilt_position"]),
    test.case("noset_stop", set_state=False, features_reg=CoverEntityFeature.STOP, features_state=0, expected_action_types=["stop"]),
    test.case("set_none", set_state=True, features_reg=0, features_state=0, expected_action_types=[]),
    test.case("set_close_tilt", set_state=True, features_reg=0, features_state=CoverEntityFeature.CLOSE_TILT, expected_action_types=["close_tilt"]),
    test.case("set_close", set_state=True, features_reg=0, features_state=CoverEntityFeature.CLOSE, expected_action_types=["close"]),
    test.case("set_open_tilt", set_state=True, features_reg=0, features_state=CoverEntityFeature.OPEN_TILT, expected_action_types=["open_tilt"]),
    test.case("set_open", set_state=True, features_reg=0, features_state=CoverEntityFeature.OPEN, expected_action_types=["open"]),
    test.case("set_set_position", set_state=True, features_reg=0, features_state=CoverEntityFeature.SET_POSITION, expected_action_types=["set_position"]),
    test.case("set_set_tilt_position", set_state=True, features_reg=0, features_state=CoverEntityFeature.SET_TILT_POSITION, expected_action_types=["set_tilt_position"]),
    test.case("set_stop", set_state=True, features_reg=0, features_state=CoverEntityFeature.STOP, expected_action_types=["stop"]),
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
    """Test we get the expected actions from a cover."""
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
            entity_entry.entity_id, "attributes", {"supported_features": features_state}
        )
    await hass.async_block_till_done()

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
        supported_features=CoverEntityFeature.CLOSE,
    )
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": action,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": True},
        }
        for action in ("close",)
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
) -> None:
    """Test we get the expected capabilities from a cover action."""
    ent = MockCover(
        name="Set position cover",
        unique_id="unique_set_pos_cover",
        current_cover_position=50,
        supported_features=CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.OPEN_TILT
        | CoverEntityFeature.CLOSE_TILT
        | CoverEntityFeature.STOP_TILT,
    )
    setup_test_component_platform(hass, DOMAIN, [ent])
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

    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(len(actions)).to_equal(5)
    action_types = {action["type"] for action in actions}
    expect(action_types).to_equal({"open", "close", "stop", "open_tilt", "close_tilt"})
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        expect(capabilities).to_equal({"extra_fields": []})


@test
async def get_action_capabilities_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected capabilities from a cover action."""
    ent = MockCover(
        name="Set position cover",
        unique_id="unique_set_pos_cover",
        current_cover_position=50,
        supported_features=CoverEntityFeature.OPEN
        | CoverEntityFeature.CLOSE
        | CoverEntityFeature.STOP
        | CoverEntityFeature.OPEN_TILT
        | CoverEntityFeature.CLOSE_TILT
        | CoverEntityFeature.STOP_TILT,
    )
    setup_test_component_platform(hass, DOMAIN, [ent])
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

    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(len(actions)).to_equal(5)
    action_types = {action["type"] for action in actions}
    expect(action_types).to_equal({"open", "close", "stop", "open_tilt", "close_tilt"})
    for action in actions:
        action["entity_id"] = entity_registry.async_get(action["entity_id"]).entity_id
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        expect(capabilities).to_equal({"extra_fields": []})


@test
async def get_action_capabilities_set_pos(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test we get the expected capabilities from a cover action."""
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
                "name": "position",
                "optional": True,
                "required": False,
                "type": "integer",
                "default": 0,
                "valueMax": 100,
                "valueMin": 0,
            }
        ]
    }
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(len(actions)).to_equal(4)
    action_types = {action["type"] for action in actions}
    expect(action_types).to_equal({"set_position", "open", "close", "stop"})
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        if action["type"] == "set_position":
            expect(capabilities).to_equal(expected_capabilities)
        else:
            expect(capabilities).to_equal({"extra_fields": []})


@test
async def get_action_capabilities_set_tilt_pos(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test we get the expected capabilities from a cover action."""
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
                "name": "position",
                "optional": True,
                "required": False,
                "type": "integer",
                "default": 0,
                "valueMax": 100,
                "valueMin": 0,
            }
        ]
    }
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(len(actions)).to_equal(5)
    action_types = {action["type"] for action in actions}
    expect(action_types).to_equal(
        {
            "open",
            "close",
            "set_tilt_position",
            "open_tilt",
            "close_tilt",
        }
    )
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        if action["type"] == "set_tilt_position":
            expect(capabilities).to_equal(expected_capabilities)
        else:
            expect(capabilities).to_equal({"extra_fields": []})


@test
async def action(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test for cover actions."""
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
                        "trigger": {"platform": "event", "event_type": "test_event_open"},
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "open",
                        },
                    },
                    {
                        "trigger": {"platform": "event", "event_type": "test_event_close"},
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "close",
                        },
                    },
                    {
                        "trigger": {"platform": "event", "event_type": "test_event_stop"},
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "stop",
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    open_calls = async_mock_service(hass, "cover", "open_cover")
    close_calls = async_mock_service(hass, "cover", "close_cover")
    stop_calls = async_mock_service(hass, "cover", "stop_cover")

    hass.bus.async_fire("test_event_open")
    await hass.async_block_till_done()
    expect(len(open_calls)).to_equal(1)
    expect(len(close_calls)).to_equal(0)
    expect(len(stop_calls)).to_equal(0)

    hass.bus.async_fire("test_event_close")
    await hass.async_block_till_done()
    expect(len(open_calls)).to_equal(1)
    expect(len(close_calls)).to_equal(1)
    expect(len(stop_calls)).to_equal(0)

    hass.bus.async_fire("test_event_stop")
    await hass.async_block_till_done()
    expect(len(open_calls)).to_equal(1)
    expect(len(close_calls)).to_equal(1)
    expect(len(stop_calls)).to_equal(1)

    expect(open_calls[0].domain).to_equal(DOMAIN)
    expect(open_calls[0].service).to_equal("open_cover")
    expect(open_calls[0].data).to_equal({"entity_id": entry.entity_id})
    expect(close_calls[0].domain).to_equal(DOMAIN)
    expect(close_calls[0].service).to_equal("close_cover")
    expect(close_calls[0].data).to_equal({"entity_id": entry.entity_id})
    expect(stop_calls[0].domain).to_equal(DOMAIN)
    expect(stop_calls[0].service).to_equal("stop_cover")
    expect(stop_calls[0].data).to_equal({"entity_id": entry.entity_id})


@test
async def action_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test for cover actions."""
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
                        "trigger": {"platform": "event", "event_type": "test_event_open"},
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

    open_calls = async_mock_service(hass, "cover", "open_cover")

    hass.bus.async_fire("test_event_open")
    await hass.async_block_till_done()
    expect(len(open_calls)).to_equal(1)

    expect(open_calls[0].domain).to_equal(DOMAIN)
    expect(open_calls[0].service).to_equal("open_cover")
    expect(open_calls[0].data).to_equal({"entity_id": entry.entity_id})


@test
async def action_tilt(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test for cover tilt actions."""
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
                        "trigger": {"platform": "event", "event_type": "test_event_open"},
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "open_tilt",
                        },
                    },
                    {
                        "trigger": {"platform": "event", "event_type": "test_event_close"},
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "close_tilt",
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    open_calls = async_mock_service(hass, "cover", "open_cover_tilt")
    close_calls = async_mock_service(hass, "cover", "close_cover_tilt")

    hass.bus.async_fire("test_event_open")
    await hass.async_block_till_done()
    expect(len(open_calls)).to_equal(1)
    expect(len(close_calls)).to_equal(0)

    hass.bus.async_fire("test_event_close")
    await hass.async_block_till_done()
    expect(len(open_calls)).to_equal(1)
    expect(len(close_calls)).to_equal(1)

    hass.bus.async_fire("test_event_stop")
    await hass.async_block_till_done()
    expect(len(open_calls)).to_equal(1)
    expect(len(close_calls)).to_equal(1)

    expect(open_calls[0].domain).to_equal(DOMAIN)
    expect(open_calls[0].service).to_equal("open_cover_tilt")
    expect(open_calls[0].data).to_equal({"entity_id": entry.entity_id})
    expect(close_calls[0].domain).to_equal(DOMAIN)
    expect(close_calls[0].service).to_equal("close_cover_tilt")
    expect(close_calls[0].data).to_equal({"entity_id": entry.entity_id})


@test
async def action_set_position(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _mock_cover_entities: list[MockCover] = Depends(mock_cover_entities_fixture),
) -> None:
    """Test for cover set position actions."""
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
                            "event_type": "test_event_set_pos",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "set_position",
                            "position": 25,
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_set_tilt_pos",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "set_tilt_position",
                            "position": 75,
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    cover_pos_calls = async_mock_service(hass, "cover", "set_cover_position")
    tilt_pos_calls = async_mock_service(hass, "cover", "set_cover_tilt_position")

    hass.bus.async_fire("test_event_set_pos")
    await hass.async_block_till_done()
    expect(len(cover_pos_calls)).to_equal(1)
    expect(len(tilt_pos_calls)).to_equal(0)

    hass.bus.async_fire("test_event_set_tilt_pos")
    await hass.async_block_till_done()
    expect(len(cover_pos_calls)).to_equal(1)
    expect(len(tilt_pos_calls)).to_equal(1)

    expect(cover_pos_calls[0].domain).to_equal(DOMAIN)
    expect(cover_pos_calls[0].service).to_equal("set_cover_position")
    expect(cover_pos_calls[0].data).to_equal(
        {"entity_id": entry.entity_id, "position": 25}
    )
    expect(tilt_pos_calls[0].domain).to_equal(DOMAIN)
    expect(tilt_pos_calls[0].service).to_equal("set_cover_tilt_position")
    expect(tilt_pos_calls[0].data).to_equal(
        {"entity_id": entry.entity_id, "tilt_position": 75}
    )
