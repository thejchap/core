"""The tests for Climate device actions (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test
import voluptuous_serialize

from homeassistant.components import automation
from homeassistant.components.climate import DOMAIN, HVACMode, const, device_action
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.const import EntityCategory
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
        expected_action_types=["set_hvac_mode"],
    ),
    test.case(
        "noset_preset_mode",
        set_state=False,
        features_reg=const.ClimateEntityFeature.PRESET_MODE,
        features_state=0,
        expected_action_types=["set_hvac_mode", "set_preset_mode"],
    ),
    test.case(
        "set_none",
        set_state=True,
        features_reg=0,
        features_state=0,
        expected_action_types=["set_hvac_mode"],
    ),
    test.case(
        "set_preset_mode",
        set_state=True,
        features_reg=0,
        features_state=const.ClimateEntityFeature.PRESET_MODE,
        expected_action_types=["set_hvac_mode", "set_preset_mode"],
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
    """Test we get the expected actions from a climate."""
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
        hidden_by=RegistryEntryHider.INTEGRATION,
        entity_category=None,
    ),
    test.case(
        "user",
        hidden_by=RegistryEntryHider.USER,
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
        for action in ("set_hvac_mode",)
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
        HVACMode.COOL,
        {
            const.ATTR_HVAC_MODES: [HVACMode.COOL, HVACMode.OFF],
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY],
        },
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
                            "event_type": "test_event_set_hvac_mode",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "set_hvac_mode",
                            "hvac_mode": HVACMode.OFF,
                        },
                    },
                    {
                        "trigger": {
                            "platform": "event",
                            "event_type": "test_event_set_preset_mode",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "set_preset_mode",
                            "preset_mode": const.PRESET_AWAY,
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    set_hvac_mode_calls = async_mock_service(hass, "climate", "set_hvac_mode")
    set_preset_mode_calls = async_mock_service(hass, "climate", "set_preset_mode")

    hass.bus.async_fire("test_event_set_hvac_mode")
    await hass.async_block_till_done()
    expect(len(set_hvac_mode_calls)).to_equal(1)
    expect(len(set_preset_mode_calls)).to_equal(0)

    hass.bus.async_fire("test_event_set_preset_mode")
    await hass.async_block_till_done()
    expect(len(set_hvac_mode_calls)).to_equal(1)
    expect(len(set_preset_mode_calls)).to_equal(1)

    expect(set_hvac_mode_calls[0].domain).to_equal(DOMAIN)
    expect(set_hvac_mode_calls[0].service).to_equal("set_hvac_mode")
    expect(set_hvac_mode_calls[0].data).to_equal(
        {
            "entity_id": entry.entity_id,
            "hvac_mode": const.HVACMode.OFF,
        }
    )
    expect(set_preset_mode_calls[0].domain).to_equal(DOMAIN)
    expect(set_preset_mode_calls[0].service).to_equal("set_preset_mode")
    expect(set_preset_mode_calls[0].data).to_equal(
        {
            "entity_id": entry.entity_id,
            "preset_mode": const.PRESET_AWAY,
        }
    )


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
        HVACMode.COOL,
        {
            const.ATTR_HVAC_MODES: [HVACMode.COOL, HVACMode.OFF],
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY],
        },
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
                            "event_type": "test_event_set_hvac_mode",
                        },
                        "action": {
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.entity_id,
                            "type": "set_hvac_mode",
                            "hvac_mode": HVACMode.OFF,
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    set_hvac_mode_calls = async_mock_service(hass, "climate", "set_hvac_mode")

    hass.bus.async_fire("test_event_set_hvac_mode")
    await hass.async_block_till_done()
    expect(len(set_hvac_mode_calls)).to_equal(1)

    expect(set_hvac_mode_calls[0].domain).to_equal(DOMAIN)
    expect(set_hvac_mode_calls[0].service).to_equal("set_hvac_mode")
    expect(set_hvac_mode_calls[0].data).to_equal(
        {
            "entity_id": entry.entity_id,
            "hvac_mode": const.HVACMode.OFF,
        }
    )


@test.cases(
    test.case(
        "noset_hvac_modes",
        set_state=False,
        capabilities_reg={const.ATTR_HVAC_MODES: [HVACMode.COOL, HVACMode.OFF]},
        capabilities_state={},
        action_type="set_hvac_mode",
        expected_capabilities=[
            {
                "name": "hvac_mode",
                "options": [("cool", "cool"), ("off", "off")],
                "required": True,
                "type": "select",
            }
        ],
    ),
    test.case(
        "noset_preset_modes",
        set_state=False,
        capabilities_reg={
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY]
        },
        capabilities_state={},
        action_type="set_preset_mode",
        expected_capabilities=[
            {
                "name": "preset_mode",
                "options": [("home", "home"), ("away", "away")],
                "required": True,
                "type": "select",
            }
        ],
    ),
    test.case(
        "set_hvac_modes",
        set_state=True,
        capabilities_reg={},
        capabilities_state={const.ATTR_HVAC_MODES: [HVACMode.COOL, HVACMode.OFF]},
        action_type="set_hvac_mode",
        expected_capabilities=[
            {
                "name": "hvac_mode",
                "options": [("cool", "cool"), ("off", "off")],
                "required": True,
                "type": "select",
            }
        ],
    ),
    test.case(
        "set_preset_modes",
        set_state=True,
        capabilities_reg={},
        capabilities_state={
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY]
        },
        action_type="set_preset_mode",
        expected_capabilities=[
            {
                "name": "preset_mode",
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
    action_type: str,
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
            HVACMode.COOL,
            capabilities_state,
        )

    caps = await device_action.async_get_action_capabilities(
        hass,
        {
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": entity_entry.id,
            "type": action_type,
        },
    )

    expect(caps).to_be_truthy()
    expect("extra_fields" in caps).to_be_truthy()

    expect(
        voluptuous_serialize.convert(
            caps["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(expected_capabilities)


@test.cases(
    test.case(
        "noset_hvac_modes",
        set_state=False,
        capabilities_reg={const.ATTR_HVAC_MODES: [HVACMode.COOL, HVACMode.OFF]},
        capabilities_state={},
        action_type="set_hvac_mode",
        expected_capabilities=[
            {
                "name": "hvac_mode",
                "options": [("cool", "cool"), ("off", "off")],
                "required": True,
                "type": "select",
            }
        ],
    ),
    test.case(
        "noset_preset_modes",
        set_state=False,
        capabilities_reg={
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY]
        },
        capabilities_state={},
        action_type="set_preset_mode",
        expected_capabilities=[
            {
                "name": "preset_mode",
                "options": [("home", "home"), ("away", "away")],
                "required": True,
                "type": "select",
            }
        ],
    ),
    test.case(
        "set_hvac_modes",
        set_state=True,
        capabilities_reg={},
        capabilities_state={const.ATTR_HVAC_MODES: [HVACMode.COOL, HVACMode.OFF]},
        action_type="set_hvac_mode",
        expected_capabilities=[
            {
                "name": "hvac_mode",
                "options": [("cool", "cool"), ("off", "off")],
                "required": True,
                "type": "select",
            }
        ],
    ),
    test.case(
        "set_preset_modes",
        set_state=True,
        capabilities_reg={},
        capabilities_state={
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY]
        },
        action_type="set_preset_mode",
        expected_capabilities=[
            {
                "name": "preset_mode",
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
    action_type: str,
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
            HVACMode.COOL,
            capabilities_state,
        )

    caps = await device_action.async_get_action_capabilities(
        hass,
        {
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": entity_entry.entity_id,
            "type": action_type,
        },
    )

    expect(caps).to_be_truthy()
    expect("extra_fields" in caps).to_be_truthy()

    expect(
        voluptuous_serialize.convert(
            caps["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(expected_capabilities)


@test.cases(
    test.case(
        "set_hvac_mode",
        action_type="set_hvac_mode",
        capability_name="hvac_mode",
    ),
    test.case(
        "set_preset_mode",
        action_type="set_preset_mode",
        capability_name="preset_mode",
    ),
)
async def capabilities_missing_entity(
    hass: HomeAssistant = Depends(_trigger_executor),
    *,
    action_type: str,
    capability_name: str,
) -> None:
    """Test getting capabilities."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)

    caps = await device_action.async_get_action_capabilities(
        hass,
        {
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": f"{DOMAIN}.test_5678",
            "type": action_type,
        },
    )

    expected_capabilities = [
        {
            "name": capability_name,
            "options": [],
            "required": True,
            "type": "select",
        }
    ]

    expect(caps).to_be_truthy()
    expect("extra_fields" in caps).to_be_truthy()

    expect(
        voluptuous_serialize.convert(
            caps["extra_fields"], custom_serializer=cv.custom_serializer
        )
    ).to_equal(expected_capabilities)
