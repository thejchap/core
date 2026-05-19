"""The tests for Humidifier device actions (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test
import voluptuous_serialize

from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.humidifier import DOMAIN, const, device_action
from homeassistant.const import STATE_ON, EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)
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
        "noset_modes",
        set_state=False,
        features_reg=const.HumidifierEntityFeature.MODES,
        features_state=0,
        expected_action_types=["set_mode"],
    ),
    test.case(
        "set_none",
        set_state=True,
        features_reg=0,
        features_state=0,
        expected_action_types=[],
    ),
    test.case(
        "set_modes",
        set_state=True,
        features_reg=0,
        features_state=const.HumidifierEntityFeature.MODES,
        expected_action_types=["set_mode"],
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
    """Test we get the expected actions from a humidifier."""
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
    basic_action_types = ["set_humidity", "turn_on", "turn_off", "toggle"]
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
        supported_features=0,
    )
    basic_action_types = ["set_humidity", "turn_on", "turn_off", "toggle"]
    expected_actions = [
        {
            "domain": DOMAIN,
            "type": action,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": True},
        }
        for action in basic_action_types
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
    """Test for actions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY]},
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
                            "event_type": "test_event_turn_off",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "turn_off",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_turn_on",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "turn_on",
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_toggle",
                        },
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
                            "event_type": "test_event_set_humidity",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "set_humidity",
                            "humidity": 35,
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_set_mode",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "set_mode",
                            "mode": const.MODE_AWAY,
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    set_humidity_calls = async_mock_service(hass, "humidifier", "set_humidity")
    set_mode_calls = async_mock_service(hass, "humidifier", "set_mode")
    turn_on_calls = async_mock_service(hass, "humidifier", "turn_on")
    turn_off_calls = async_mock_service(hass, "humidifier", "turn_off")
    toggle_calls = async_mock_service(hass, "humidifier", "toggle")

    expect(len(set_humidity_calls)).to_equal(0)
    expect(len(set_mode_calls)).to_equal(0)
    expect(len(turn_on_calls)).to_equal(0)
    expect(len(turn_off_calls)).to_equal(0)
    expect(len(toggle_calls)).to_equal(0)

    hass.bus.async_fire("test_event_set_humidity")
    await hass.async_block_till_done()
    expect(len(set_humidity_calls)).to_equal(1)
    expect(len(set_mode_calls)).to_equal(0)
    expect(len(turn_on_calls)).to_equal(0)
    expect(len(turn_off_calls)).to_equal(0)
    expect(len(toggle_calls)).to_equal(0)

    hass.bus.async_fire("test_event_set_mode")
    await hass.async_block_till_done()
    expect(len(set_humidity_calls)).to_equal(1)
    expect(len(set_mode_calls)).to_equal(1)
    expect(len(turn_on_calls)).to_equal(0)
    expect(len(turn_off_calls)).to_equal(0)
    expect(len(toggle_calls)).to_equal(0)

    hass.bus.async_fire("test_event_turn_off")
    await hass.async_block_till_done()
    expect(len(set_humidity_calls)).to_equal(1)
    expect(len(set_mode_calls)).to_equal(1)
    expect(len(turn_on_calls)).to_equal(0)
    expect(len(turn_off_calls)).to_equal(1)
    expect(len(toggle_calls)).to_equal(0)

    hass.bus.async_fire("test_event_turn_on")
    await hass.async_block_till_done()
    expect(len(set_humidity_calls)).to_equal(1)
    expect(len(set_mode_calls)).to_equal(1)
    expect(len(turn_on_calls)).to_equal(1)
    expect(len(turn_off_calls)).to_equal(1)
    expect(len(toggle_calls)).to_equal(0)

    hass.bus.async_fire("test_event_toggle")
    await hass.async_block_till_done()
    expect(len(set_humidity_calls)).to_equal(1)
    expect(len(set_mode_calls)).to_equal(1)
    expect(len(turn_on_calls)).to_equal(1)
    expect(len(turn_off_calls)).to_equal(1)
    expect(len(toggle_calls)).to_equal(1)

    expect(set_humidity_calls[0].domain).to_equal(DOMAIN)
    expect(set_humidity_calls[0].service).to_equal("set_humidity")
    expect(set_humidity_calls[0].data).to_equal(
        {"entity_id": entry.entity_id, "humidity": 35}
    )
    expect(set_mode_calls[0].domain).to_equal(DOMAIN)
    expect(set_mode_calls[0].service).to_equal("set_mode")
    expect(set_mode_calls[0].data).to_equal(
        {"entity_id": entry.entity_id, "mode": "away"}
    )
    expect(turn_on_calls[0].domain).to_equal(DOMAIN)
    expect(turn_on_calls[0].service).to_equal("turn_on")
    expect(turn_on_calls[0].data).to_equal({"entity_id": entry.entity_id})
    expect(turn_off_calls[0].domain).to_equal(DOMAIN)
    expect(turn_off_calls[0].service).to_equal("turn_off")
    expect(turn_off_calls[0].data).to_equal({"entity_id": entry.entity_id})
    expect(toggle_calls[0].domain).to_equal(DOMAIN)
    expect(toggle_calls[0].service).to_equal("toggle")
    expect(toggle_calls[0].data).to_equal({"entity_id": entry.entity_id})


@test
async def action_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test for actions."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )

    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY]},
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
                            "event_type": "test_event_set_mode",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.entity_id,
                            "type": "set_mode",
                            "mode": const.MODE_AWAY,
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    set_mode_calls = async_mock_service(hass, "humidifier", "set_mode")

    hass.bus.async_fire("test_event_set_mode")
    await hass.async_block_till_done()
    expect(len(set_mode_calls)).to_equal(1)

    expect(set_mode_calls[0].domain).to_equal(DOMAIN)
    expect(set_mode_calls[0].service).to_equal("set_mode")
    expect(set_mode_calls[0].data).to_equal(
        {"entity_id": entry.entity_id, "mode": "away"}
    )


@test.cases(
    test.case(
        "noset_set_humidity",
        set_state=False,
        capabilities_reg={},
        capabilities_state={},
        action="set_humidity",
        expected_capabilities=[
            {"name": "humidity", "required": True, "type": "integer"}
        ],
    ),
    test.case(
        "noset_set_mode_empty",
        set_state=False,
        capabilities_reg={},
        capabilities_state={},
        action="set_mode",
        expected_capabilities=[
            {"name": "mode", "options": [], "required": True, "type": "select"}
        ],
    ),
    test.case(
        "noset_set_mode_modes",
        set_state=False,
        capabilities_reg={const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY]},
        capabilities_state={},
        action="set_mode",
        expected_capabilities=[
            {
                "name": "mode",
                "options": [("home", "home"), ("away", "away")],
                "required": True,
                "type": "select",
            }
        ],
    ),
    test.case(
        "set_set_humidity",
        set_state=True,
        capabilities_reg={},
        capabilities_state={},
        action="set_humidity",
        expected_capabilities=[
            {"name": "humidity", "required": True, "type": "integer"}
        ],
    ),
    test.case(
        "set_set_mode_empty",
        set_state=True,
        capabilities_reg={},
        capabilities_state={},
        action="set_mode",
        expected_capabilities=[
            {"name": "mode", "options": [], "required": True, "type": "select"}
        ],
    ),
    test.case(
        "set_set_mode_modes",
        set_state=True,
        capabilities_reg={},
        capabilities_state={const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY]},
        action="set_mode",
        expected_capabilities=[
            {
                "name": "mode",
                "options": [("home", "home"), ("away", "away")],
                "required": True,
                "type": "select",
            }
        ],
    ),
)
async def capabilities(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    set_state: bool,
    capabilities_reg: dict,
    capabilities_state: dict,
    action: str,
    expected_capabilities: list[dict],
) -> None:
    """Test getting capabilities."""
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
        capabilities=capabilities_reg,
    )
    if set_state:
        hass.states.async_set(
            f"{DOMAIN}.test_5678",
            STATE_ON,
            capabilities_state,
        )

    capabilities_result = await device_action.async_get_action_capabilities(
        hass,
        {
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": entity_entry.id,
            "type": action,
        },
    )

    expect(capabilities_result).to_be_truthy()
    expect("extra_fields" in capabilities_result).to_be_truthy()

    expect(
        voluptuous_serialize.convert(
            capabilities_result["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(expected_capabilities)


@test.cases(
    test.case(
        "noset_set_humidity",
        set_state=False,
        capabilities_reg={},
        capabilities_state={},
        action="set_humidity",
        expected_capabilities=[
            {"name": "humidity", "required": True, "type": "integer"}
        ],
    ),
    test.case(
        "noset_set_mode_empty",
        set_state=False,
        capabilities_reg={},
        capabilities_state={},
        action="set_mode",
        expected_capabilities=[
            {"name": "mode", "options": [], "required": True, "type": "select"}
        ],
    ),
    test.case(
        "noset_set_mode_modes",
        set_state=False,
        capabilities_reg={const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY]},
        capabilities_state={},
        action="set_mode",
        expected_capabilities=[
            {
                "name": "mode",
                "options": [("home", "home"), ("away", "away")],
                "required": True,
                "type": "select",
            }
        ],
    ),
    test.case(
        "set_set_humidity",
        set_state=True,
        capabilities_reg={},
        capabilities_state={},
        action="set_humidity",
        expected_capabilities=[
            {"name": "humidity", "required": True, "type": "integer"}
        ],
    ),
    test.case(
        "set_set_mode_empty",
        set_state=True,
        capabilities_reg={},
        capabilities_state={},
        action="set_mode",
        expected_capabilities=[
            {"name": "mode", "options": [], "required": True, "type": "select"}
        ],
    ),
    test.case(
        "set_set_mode_modes",
        set_state=True,
        capabilities_reg={},
        capabilities_state={const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY]},
        action="set_mode",
        expected_capabilities=[
            {
                "name": "mode",
                "options": [("home", "home"), ("away", "away")],
                "required": True,
                "type": "select",
            }
        ],
    ),
)
async def capabilities_legacy(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    set_state: bool,
    capabilities_reg: dict,
    capabilities_state: dict,
    action: str,
    expected_capabilities: list[dict],
) -> None:
    """Test getting capabilities."""
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
        capabilities=capabilities_reg,
    )
    if set_state:
        hass.states.async_set(
            f"{DOMAIN}.test_5678",
            STATE_ON,
            capabilities_state,
        )

    capabilities_result = await device_action.async_get_action_capabilities(
        hass,
        {
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": entity_entry.entity_id,
            "type": action,
        },
    )

    expect(capabilities_result).to_be_truthy()
    expect("extra_fields" in capabilities_result).to_be_truthy()

    expect(
        voluptuous_serialize.convert(
            capabilities_result["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(expected_capabilities)


@test.cases(
    test.case(
        "set_humidity",
        action="set_humidity",
        capability_name="humidity",
        extra={"type": "integer"},
    ),
)
async def capabilities_missing_entity(
    hass: HomeAssistant = Depends(_trigger_executor),
    *,
    action: str,
    capability_name: str,
    extra: dict,
) -> None:
    """Test getting capabilities."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)

    capabilities_result = await device_action.async_get_action_capabilities(
        hass,
        {
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": f"{DOMAIN}.test_5678",
            "type": action,
        },
    )

    expected_capabilities = [
        {
            "name": capability_name,
            "required": True,
            **extra,
        }
    ]

    expect(capabilities_result).to_be_truthy()
    expect("extra_fields" in capabilities_result).to_be_truthy()

    expect(
        voluptuous_serialize.convert(
            capabilities_result["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(expected_capabilities)
