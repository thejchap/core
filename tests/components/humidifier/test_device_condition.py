"""The tests for Humidifier device conditions (tryke port)."""

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test
import voluptuous_serialize

from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.humidifier import DOMAIN, const, device_condition
from homeassistant.const import ATTR_MODE, STATE_OFF, STATE_ON, EntityCategory
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.entity_registry import RegistryEntryHider
from homeassistant.setup import async_setup_component

from tests.common import MockConfigEntry, async_get_device_automations
from tests.components.humidifier._fixtures import service_calls as service_calls_fixture
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)


@fixture
def _condition_executor() -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@test.cases(
    test.case(
        "noset_none",
        set_state=False,
        features_reg=0,
        features_state=0,
        expected_condition_types=[],
    ),
    test.case(
        "noset_modes",
        set_state=False,
        features_reg=const.HumidifierEntityFeature.MODES,
        features_state=0,
        expected_condition_types=["is_mode"],
    ),
    test.case(
        "set_none",
        set_state=True,
        features_reg=0,
        features_state=0,
        expected_condition_types=[],
    ),
    test.case(
        "set_modes",
        set_state=True,
        features_reg=0,
        features_state=const.HumidifierEntityFeature.MODES,
        expected_condition_types=["is_mode"],
    ),
)
async def get_conditions(
    _t: int = Depends(_condition_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    *,
    set_state: bool,
    features_reg: int,
    features_state: int,
    expected_condition_types: list[str],
) -> None:
    """Test we get the expected conditions from a humidifier."""
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
    expected_conditions = []
    basic_condition_types = ["is_on", "is_off"]
    expected_conditions += [
        {
            "condition": "device",
            "domain": DOMAIN,
            "type": condition,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
        for condition in basic_condition_types
    ]
    expected_conditions += [
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
    _t: int = Depends(_condition_executor),
    hass: HomeAssistant = Depends(hass_fixture),
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
        for condition in ("is_off", "is_on")
    ]
    conditions = await async_get_device_automations(
        hass, DeviceAutomationType.CONDITION, device_entry.id
    )
    expect(conditions).to_equal(unordered(expected_conditions))


@test
async def if_state(
    _t: int = Depends(_condition_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
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

    hass.states.async_set(entry.entity_id, STATE_ON, {ATTR_MODE: const.MODE_AWAY})

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
                                "type": "is_on",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_on {{ trigger.platform }}"
                                    " - {{ trigger.event.event_type }}"
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
                                "type": "is_off",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "is_off {{ trigger.platform }}"
                                    " - {{ trigger.event.event_type }}"
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
                                "type": "is_mode",
                                "mode": "away",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": "is_mode - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("is_on event - test_event1")

    hass.states.async_set(entry.entity_id, STATE_OFF)
    hass.bus.async_fire("test_event1")
    hass.bus.async_fire("test_event2")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal("is_off event - test_event2")

    hass.states.async_set(entry.entity_id, STATE_ON, {ATTR_MODE: const.MODE_AWAY})

    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(3)
    expect(service_calls[2].data["some"]).to_equal("is_mode - event - test_event3")

    hass.states.async_set(entry.entity_id, STATE_ON, {ATTR_MODE: const.MODE_HOME})

    # Should not fire
    hass.bus.async_fire("test_event3")
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)


@test
async def if_state_legacy(
    _t: int = Depends(_condition_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
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

    hass.states.async_set(entry.entity_id, STATE_ON, {ATTR_MODE: const.MODE_AWAY})

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
                                "type": "is_mode",
                                "mode": "away",
                            }
                        ],
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": "is_mode - {{ trigger.platform }} - {{ trigger.event.event_type }}"
                            },
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(0)

    hass.states.async_set(entry.entity_id, STATE_ON, {ATTR_MODE: const.MODE_AWAY})

    hass.bus.async_fire("test_event1")
    await hass.async_block_till_done()

    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("is_mode - event - test_event1")


@test.cases(
    test.case(
        "noset_is_mode_empty",
        set_state=False,
        capabilities_reg={},
        capabilities_state={},
        condition="is_mode",
        expected_capabilities=[
            {"name": "mode", "options": [], "required": True, "type": "select"}
        ],
    ),
    test.case(
        "noset_is_mode_modes",
        set_state=False,
        capabilities_reg={const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY]},
        capabilities_state={},
        condition="is_mode",
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
        "noset_is_off",
        set_state=False,
        capabilities_reg={},
        capabilities_state={},
        condition="is_off",
        expected_capabilities=[
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ],
    ),
    test.case(
        "noset_is_on",
        set_state=False,
        capabilities_reg={},
        capabilities_state={},
        condition="is_on",
        expected_capabilities=[
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ],
    ),
    test.case(
        "set_is_mode_empty",
        set_state=True,
        capabilities_reg={},
        capabilities_state={},
        condition="is_mode",
        expected_capabilities=[
            {"name": "mode", "options": [], "required": True, "type": "select"}
        ],
    ),
    test.case(
        "set_is_mode_modes",
        set_state=True,
        capabilities_reg={},
        capabilities_state={const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY]},
        condition="is_mode",
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
        "set_is_off",
        set_state=True,
        capabilities_reg={},
        capabilities_state={},
        condition="is_off",
        expected_capabilities=[
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ],
    ),
    test.case(
        "set_is_on",
        set_state=True,
        capabilities_reg={},
        capabilities_state={},
        condition="is_on",
        expected_capabilities=[
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ],
    ),
)
async def capabilities(
    _t: int = Depends(_condition_executor),
    hass: HomeAssistant = Depends(hass_fixture),
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
            STATE_ON,
            capabilities_state,
        )

    capabilities_result = await device_condition.async_get_condition_capabilities(
        hass,
        {
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": entity_entry.id,
            "type": condition,
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
        "noset_is_mode_empty",
        set_state=False,
        capabilities_reg={},
        capabilities_state={},
        condition="is_mode",
        expected_capabilities=[
            {"name": "mode", "options": [], "required": True, "type": "select"}
        ],
    ),
    test.case(
        "noset_is_mode_modes",
        set_state=False,
        capabilities_reg={const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY]},
        capabilities_state={},
        condition="is_mode",
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
        "noset_is_off",
        set_state=False,
        capabilities_reg={},
        capabilities_state={},
        condition="is_off",
        expected_capabilities=[
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ],
    ),
    test.case(
        "noset_is_on",
        set_state=False,
        capabilities_reg={},
        capabilities_state={},
        condition="is_on",
        expected_capabilities=[
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ],
    ),
    test.case(
        "set_is_mode_empty",
        set_state=True,
        capabilities_reg={},
        capabilities_state={},
        condition="is_mode",
        expected_capabilities=[
            {"name": "mode", "options": [], "required": True, "type": "select"}
        ],
    ),
    test.case(
        "set_is_mode_modes",
        set_state=True,
        capabilities_reg={},
        capabilities_state={const.ATTR_AVAILABLE_MODES: [const.MODE_HOME, const.MODE_AWAY]},
        condition="is_mode",
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
        "set_is_off",
        set_state=True,
        capabilities_reg={},
        capabilities_state={},
        condition="is_off",
        expected_capabilities=[
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ],
    ),
    test.case(
        "set_is_on",
        set_state=True,
        capabilities_reg={},
        capabilities_state={},
        condition="is_on",
        expected_capabilities=[
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ],
    ),
)
async def capabilities_legacy(
    _t: int = Depends(_condition_executor),
    hass: HomeAssistant = Depends(hass_fixture),
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
            STATE_ON,
            capabilities_state,
        )

    capabilities_result = await device_condition.async_get_condition_capabilities(
        hass,
        {
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": entity_entry.entity_id,
            "type": condition,
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
        "is_mode",
        condition="is_mode",
        capability_name="mode",
        extra={"type": "select", "options": []},
    ),
)
async def capabilities_missing_entity(
    _t: int = Depends(_condition_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    *,
    condition: str,
    capability_name: str,
    extra: dict,
) -> None:
    """Test getting capabilities."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)

    capabilities_result = await device_condition.async_get_condition_capabilities(
        hass,
        {
            "domain": DOMAIN,
            "device_id": "abcdefgh",
            "entity_id": "0123456789",
            "type": condition,
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
