"""The test for light device automation (tryke port)."""

from collections.abc import Generator

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant import loader
from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.light import (
    ATTR_SUPPORTED_COLOR_MODES,
    DOMAIN,
    FLASH_LONG,
    FLASH_SHORT,
    ColorMode,
    LightEntityFeature,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.entity_registry import RegistryEntryHider
from homeassistant.setup import async_setup_component

from tests.common import (
    MockConfigEntry,
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


@fixture
def enable_custom_integrations(
    hass: HomeAssistant = Depends(_trigger_executor),
) -> Generator[None]:
    """Enable custom integrations defined in the test dir."""
    hass.data.pop(loader.DATA_CUSTOM_COMPONENTS, None)
    yield


@test
async def get_actions(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected actions from a light."""
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
        supported_features=LightEntityFeature.FLASH,
        capabilities={"supported_color_modes": ["brightness"]},
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
            "brightness_decrease",
            "brightness_increase",
            "flash",
            "turn_off",
            "turn_on",
            "toggle",
        )
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
        capabilities={"supported_color_modes": ["onoff"]},
    )
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": action,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": True},
        }
        for action in ("turn_on", "turn_off", "toggle")
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
    """Test we get the expected capabilities from a light action."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_id = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        "5678",
        device_id=device_entry.id,
    ).entity_id
    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(len(actions)).to_equal(3)
    action_types = {action["type"] for action in actions}
    expect(action_types).to_equal({"turn_on", "toggle", "turn_off"})
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        expect(capabilities).to_equal({"extra_fields": []})

    entity_registry.async_remove(entity_id)
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        expect(capabilities in ({"extra_fields": []}, {})).to_be_truthy()


_BRIGHTNESS_EXPECTED_ACTIONS = {
    "turn_on",
    "toggle",
    "turn_off",
    "brightness_increase",
    "brightness_decrease",
}
_BRIGHTNESS_EXPECTED_CAPS = {
    "turn_on": [
        {
            "name": "brightness_pct",
            "optional": True,
            "required": False,
            "type": "float",
            "valueMax": 100,
            "valueMin": 0,
        }
    ]
}
_FLASH_EXPECTED_ACTIONS = {"turn_on", "toggle", "turn_off", "flash"}
_FLASH_EXPECTED_CAPS = {
    "turn_on": [
        {
            "name": "flash",
            "optional": True,
            "required": False,
            "type": "select",
            "options": [("short", "short"), ("long", "long")],
        }
    ]
}


@test.cases(
    test.case(
        "brightness_reg",
        set_state=False,
        expected_actions=_BRIGHTNESS_EXPECTED_ACTIONS,
        supported_features_reg=0,
        supported_features_state=0,
        capabilities_reg={ATTR_SUPPORTED_COLOR_MODES: [ColorMode.BRIGHTNESS]},
        attributes_state={},
        expected_capabilities=_BRIGHTNESS_EXPECTED_CAPS,
    ),
    test.case(
        "brightness_state",
        set_state=True,
        expected_actions=_BRIGHTNESS_EXPECTED_ACTIONS,
        supported_features_reg=0,
        supported_features_state=0,
        capabilities_reg=None,
        attributes_state={ATTR_SUPPORTED_COLOR_MODES: [ColorMode.BRIGHTNESS]},
        expected_capabilities=_BRIGHTNESS_EXPECTED_CAPS,
    ),
    test.case(
        "flash_reg",
        set_state=False,
        expected_actions=_FLASH_EXPECTED_ACTIONS,
        supported_features_reg=LightEntityFeature.FLASH,
        supported_features_state=0,
        capabilities_reg=None,
        attributes_state={},
        expected_capabilities=_FLASH_EXPECTED_CAPS,
    ),
    test.case(
        "flash_state",
        set_state=True,
        expected_actions=_FLASH_EXPECTED_ACTIONS,
        supported_features_reg=0,
        supported_features_state=LightEntityFeature.FLASH,
        capabilities_reg=None,
        attributes_state={},
        expected_capabilities=_FLASH_EXPECTED_CAPS,
    ),
)
async def get_action_capabilities_features(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    set_state: bool,
    expected_actions: set[str],
    supported_features_reg: int,
    supported_features_state: int,
    capabilities_reg: dict | None,
    attributes_state: dict,
    expected_capabilities: dict,
) -> None:
    """Test we get the expected capabilities from a light action."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_id = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        "5678",
        device_id=device_entry.id,
        supported_features=supported_features_reg,
        capabilities=capabilities_reg,
    ).entity_id
    if set_state:
        hass.states.async_set(
            entity_id,
            None,
            {"supported_features": supported_features_state, **attributes_state},
        )

    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(len(actions)).to_equal(len(expected_actions))
    action_types = {action["type"] for action in actions}
    expect(action_types).to_equal(expected_actions)
    for action in actions:
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        expected = {"extra_fields": expected_capabilities.get(action["type"], [])}
        expect(capabilities).to_equal(expected)


@test.cases(
    test.case(
        "brightness_reg",
        set_state=False,
        expected_actions=_BRIGHTNESS_EXPECTED_ACTIONS,
        supported_features_reg=0,
        supported_features_state=0,
        capabilities_reg={ATTR_SUPPORTED_COLOR_MODES: [ColorMode.BRIGHTNESS]},
        attributes_state={},
        expected_capabilities=_BRIGHTNESS_EXPECTED_CAPS,
    ),
    test.case(
        "brightness_state",
        set_state=True,
        expected_actions=_BRIGHTNESS_EXPECTED_ACTIONS,
        supported_features_reg=0,
        supported_features_state=0,
        capabilities_reg=None,
        attributes_state={ATTR_SUPPORTED_COLOR_MODES: [ColorMode.BRIGHTNESS]},
        expected_capabilities=_BRIGHTNESS_EXPECTED_CAPS,
    ),
    test.case(
        "flash_reg",
        set_state=False,
        expected_actions=_FLASH_EXPECTED_ACTIONS,
        supported_features_reg=LightEntityFeature.FLASH,
        supported_features_state=0,
        capabilities_reg=None,
        attributes_state={},
        expected_capabilities=_FLASH_EXPECTED_CAPS,
    ),
    test.case(
        "flash_state",
        set_state=True,
        expected_actions=_FLASH_EXPECTED_ACTIONS,
        supported_features_reg=0,
        supported_features_state=LightEntityFeature.FLASH,
        capabilities_reg=None,
        attributes_state={},
        expected_capabilities=_FLASH_EXPECTED_CAPS,
    ),
)
async def get_action_capabilities_features_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    set_state: bool,
    expected_actions: set[str],
    supported_features_reg: int,
    supported_features_state: int,
    capabilities_reg: dict | None,
    attributes_state: dict,
    expected_capabilities: dict,
) -> None:
    """Test we get the expected capabilities from a light action."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_id = entity_registry.async_get_or_create(
        DOMAIN,
        "test",
        "5678",
        device_id=device_entry.id,
        supported_features=supported_features_reg,
        capabilities=capabilities_reg,
    ).entity_id
    if set_state:
        hass.states.async_set(
            entity_id,
            None,
            {"supported_features": supported_features_state, **attributes_state},
        )

    actions = await async_get_device_automations(
        hass, DeviceAutomationType.ACTION, device_entry.id
    )
    expect(len(actions)).to_equal(len(expected_actions))
    action_types = {action["type"] for action in actions}
    expect(action_types).to_equal(expected_actions)
    for action in actions:
        action["entity_id"] = entity_registry.async_get(action["entity_id"]).entity_id
        capabilities = await async_get_device_automation_capabilities(
            hass, DeviceAutomationType.ACTION, action
        )
        expected = {"extra_fields": expected_capabilities.get(action["type"], [])}
        expect(capabilities).to_equal(expected)


@test
async def action(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for turn_on and turn_off actions."""
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
                        "trigger": {"platform": "event", "event_type": "test_off"},
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "turn_off",
                        },
                    },
                    {
                        "trigger": {"platform": "event", "event_type": "test_on"},
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "turn_on",
                        },
                    },
                    {
                        "trigger": {"platform": "event", "event_type": "test_toggle"},
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "toggle",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_flash_short",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "flash",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_flash_long",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "flash",
                            "flash": "long",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_brightness_increase",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "brightness_increase",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_brightness_decrease",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "brightness_decrease",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_brightness",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "turn_on",
                            "brightness_pct": 75,
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    turn_on_calls = async_mock_service(hass, DOMAIN, "turn_on")
    turn_off_calls = async_mock_service(hass, DOMAIN, "turn_off")
    toggle_calls = async_mock_service(hass, DOMAIN, "toggle")

    hass.bus.async_fire("test_toggle")
    await hass.async_block_till_done()
    expect(len(toggle_calls)).to_equal(1)
    expect(toggle_calls[-1].data).to_equal({"entity_id": entry.entity_id})

    hass.bus.async_fire("test_off")
    await hass.async_block_till_done()
    expect(len(turn_off_calls)).to_equal(1)
    expect(turn_off_calls[-1].data).to_equal({"entity_id": entry.entity_id})

    hass.bus.async_fire("test_brightness_increase")
    await hass.async_block_till_done()
    expect(len(turn_on_calls)).to_equal(1)
    expect(turn_on_calls[-1].data).to_equal(
        {"entity_id": entry.entity_id, "brightness_step_pct": 10}
    )

    hass.bus.async_fire("test_brightness_decrease")
    await hass.async_block_till_done()
    expect(len(turn_on_calls)).to_equal(2)
    expect(turn_on_calls[-1].data).to_equal(
        {"entity_id": entry.entity_id, "brightness_step_pct": -10}
    )

    hass.bus.async_fire("test_brightness")
    await hass.async_block_till_done()
    expect(len(turn_on_calls)).to_equal(3)
    expect(turn_on_calls[-1].data).to_equal(
        {"entity_id": entry.entity_id, "brightness_pct": 75}
    )

    hass.bus.async_fire("test_on")
    await hass.async_block_till_done()
    expect(len(turn_on_calls)).to_equal(4)
    expect(turn_on_calls[-1].data).to_equal({"entity_id": entry.entity_id})

    hass.bus.async_fire("test_flash_short")
    await hass.async_block_till_done()
    expect(len(turn_on_calls)).to_equal(5)
    expect(turn_on_calls[-1].data).to_equal(
        {"entity_id": entry.entity_id, "flash": FLASH_SHORT}
    )

    hass.bus.async_fire("test_flash_long")
    await hass.async_block_till_done()
    expect(len(turn_on_calls)).to_equal(6)
    expect(turn_on_calls[-1].data).to_equal(
        {"entity_id": entry.entity_id, "flash": FLASH_LONG}
    )


@test
async def action_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    _custom: None = Depends(enable_custom_integrations),
) -> None:
    """Test for turn_on and turn_off actions."""
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
                        "trigger": {"platform": "event", "event_type": "test_off"},
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.entity_id,
                            "type": "turn_off",
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    turn_off_calls = async_mock_service(hass, DOMAIN, "turn_off")

    hass.bus.async_fire("test_off")
    await hass.async_block_till_done()
    expect(len(turn_off_calls)).to_equal(1)
    expect(turn_off_calls[-1].data).to_equal({"entity_id": entry.entity_id})
