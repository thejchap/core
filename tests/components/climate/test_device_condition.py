"""The tests for Climate device conditions (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test
import voluptuous_serialize

from homeassistant.components import automation
from homeassistant.components.climate import DOMAIN, HVACMode, const, device_condition
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
        expected_condition_types=["is_hvac_mode"],
    ),
    test.case(
        "noset_preset_mode",
        set_state=False,
        features_reg=const.ClimateEntityFeature.PRESET_MODE,
        features_state=0,
        expected_condition_types=["is_hvac_mode", "is_preset_mode"],
    ),
    test.case(
        "set_none",
        set_state=True,
        features_reg=0,
        features_state=0,
        expected_condition_types=["is_hvac_mode"],
    ),
    test.case(
        "set_preset_mode",
        set_state=True,
        features_reg=0,
        features_state=const.ClimateEntityFeature.PRESET_MODE,
        expected_condition_types=["is_hvac_mode", "is_preset_mode"],
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
    """Test we get the expected conditions from a climate."""
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
async def get_conditions_hidden_auxiliary(
    hass: HomeAssistant = Depends(_condition_executor),
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
        for condition in ("is_hvac_mode",)
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
                                "type": "is_hvac_mode",
                                "hvac_mode": "cool",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_hvac_mode - {{ trigger.platform }} "
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
                                "type": "is_preset_mode",
                                "preset_mode": "away",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_preset_mode - {{ trigger.platform }} "
                                    "- {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    # Should not fire, entity doesn't exist yet
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(
        entry.entity_id,
        HVACMode.COOL,
        {
            const.ATTR_PRESET_MODE: const.PRESET_AWAY,
        },
    )

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        "is_hvac_mode - event - test_event1"
    )

    hass.states.async_set(
        entry.entity_id,
        HVACMode.AUTO,
        {
            const.ATTR_PRESET_MODE: const.PRESET_AWAY,
        },
    )

    # Should not fire
    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)

    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal(
        "is_preset_mode - event - test_event2"
    )

    hass.states.async_set(
        entry.entity_id,
        HVACMode.AUTO,
        {
            const.ATTR_PRESET_MODE: const.PRESET_HOME,
        },
    )

    # Should not fire
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)


@test
async def if_state_legacy(
    hass: HomeAssistant = Depends(_condition_executor),
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
                                "type": "is_hvac_mode",
                                "hvac_mode": "cool",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_hvac_mode - {{ trigger.platform }} "
                                    "- {{ trigger.event.event_type }}"
                                )
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    hass.states.async_set(
        entry.entity_id,
        HVACMode.COOL,
    )

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal(
        "is_hvac_mode - event - test_event1"
    )


@test.cases(
    test.case(
        "noset_hvac_mode",
        set_state=False,
        capabilities_reg={const.ATTR_HVAC_MODES: [HVACMode.COOL, HVACMode.OFF]},
        capabilities_state={},
        condition="is_hvac_mode",
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
        "noset_preset_mode",
        set_state=False,
        capabilities_reg={
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY]
        },
        capabilities_state={},
        condition="is_preset_mode",
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
        "set_hvac_mode",
        set_state=True,
        capabilities_reg={},
        capabilities_state={const.ATTR_HVAC_MODES: [HVACMode.COOL, HVACMode.OFF]},
        condition="is_hvac_mode",
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
        "set_preset_mode",
        set_state=True,
        capabilities_reg={},
        capabilities_state={
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY]
        },
        condition="is_preset_mode",
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
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    set_state: bool,
    capabilities_reg: dict,
    capabilities_state: dict,
    condition: str,
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
            entity_entry.entity_id,
            HVACMode.COOL,
            capabilities_state,
        )

    caps = await device_condition.async_get_condition_capabilities(
        hass,
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": entity_entry.id,
            "type": condition,
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
        "noset_hvac_mode",
        set_state=False,
        capabilities_reg={const.ATTR_HVAC_MODES: [HVACMode.COOL, HVACMode.OFF]},
        capabilities_state={},
        condition="is_hvac_mode",
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
        "noset_preset_mode",
        set_state=False,
        capabilities_reg={
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY]
        },
        capabilities_state={},
        condition="is_preset_mode",
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
        "set_hvac_mode",
        set_state=True,
        capabilities_reg={},
        capabilities_state={const.ATTR_HVAC_MODES: [HVACMode.COOL, HVACMode.OFF]},
        condition="is_hvac_mode",
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
        "set_preset_mode",
        set_state=True,
        capabilities_reg={},
        capabilities_state={
            const.ATTR_PRESET_MODES: [const.PRESET_HOME, const.PRESET_AWAY]
        },
        condition="is_preset_mode",
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
    hass: HomeAssistant = Depends(_condition_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    set_state: bool,
    capabilities_reg: dict,
    capabilities_state: dict,
    condition: str,
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
            entity_entry.entity_id,
            HVACMode.COOL,
            capabilities_state,
        )

    caps = await device_condition.async_get_condition_capabilities(
        hass,
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": entity_entry.entity_id,
            "type": condition,
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
        "hvac_mode",
        condition="is_hvac_mode",
        capability_name="hvac_mode",
    ),
    test.case(
        "preset_mode",
        condition="is_preset_mode",
        capability_name="preset_mode",
    ),
)
async def capabilities_missing_entity(
    hass: HomeAssistant = Depends(_condition_executor),
    *,
    condition: str,
    capability_name: str,
) -> None:
    """Test getting capabilities."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)

    caps = await device_condition.async_get_condition_capabilities(
        hass,
        {
            "condition": "device",
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": "01234567890123456789012345678901",
            "type": condition,
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
