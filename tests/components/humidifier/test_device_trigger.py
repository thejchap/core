"""The tests for Humidifier device triggers (tryke port)."""

import datetime
from typing import Any

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test
import voluptuous_serialize

from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.humidifier import DOMAIN, const, device_trigger
from homeassistant.const import (
    ATTR_MODE,
    ATTR_SUPPORTED_FEATURES,
    STATE_OFF,
    STATE_ON,
    EntityCategory,
)
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import (
    config_validation as cv,
    device_registry as dr,
    entity_registry as er,
)
from homeassistant.helpers.entity_registry import RegistryEntryHider
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util

from tests.common import (
    MockConfigEntry,
    async_fire_time_changed,
    async_get_device_automations,
)
from tests.components.humidifier._fixtures import service_calls as service_calls_fixture
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
)


@fixture
def _trigger_executor() -> int:
    """Anchor fixture so async Depends() fixtures resolve under tryke."""
    return 0


@test
async def get_triggers(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test we get the expected triggers from a humidifier device."""
    config_entry = MockConfigEntry(domain="test", data={})
    config_entry.add_to_hass(hass)
    device_entry = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        connections={(dr.CONNECTION_NETWORK_MAC, "12:34:56:AB:CD:EF")},
    )
    entity_entry = entity_registry.async_get_or_create(
        DOMAIN, "test", "5678", device_id=device_entry.id
    )
    hass.states.async_set(
        entity_entry.entity_id,
        STATE_ON,
        {
            const.ATTR_HUMIDITY: 23,
            const.ATTR_CURRENT_HUMIDITY: 48,
            ATTR_MODE: "home",
            const.ATTR_AVAILABLE_MODES: ["home", "away"],
            ATTR_SUPPORTED_FEATURES: 1,
        },
    )
    humidifier_trigger_types = ["current_humidity_changed", "target_humidity_changed"]
    toggle_trigger_types = ["turned_on", "turned_off", "changed_states"]
    expected_triggers: list[dict[str, Any]] = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": trigger,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
        for trigger in humidifier_trigger_types
    ]
    expected_triggers += [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": trigger,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": False},
        }
        for trigger in toggle_trigger_types
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(triggers == unordered(expected_triggers)).to_be(True)


@test.cases(
    test.case("hidden_integration", hidden_by=RegistryEntryHider.INTEGRATION, entity_category=None),
    test.case("hidden_user", hidden_by=RegistryEntryHider.USER, entity_category=None),
    test.case("category_config", hidden_by=None, entity_category=EntityCategory.CONFIG),
    test.case("category_diagnostic", hidden_by=None, entity_category=EntityCategory.DIAGNOSTIC),
)
async def get_triggers_hidden_auxiliary(
    hidden_by: RegistryEntryHider | None,
    entity_category: EntityCategory | None,
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
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
    )
    humidifier_trigger_types = ["target_humidity_changed"]
    toggle_trigger_types = ["turned_on", "turned_off", "changed_states"]
    expected_triggers: list[dict[str, Any]] = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": trigger,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": True},
        }
        for trigger in humidifier_trigger_types
    ]
    expected_triggers += [
        {
            "platform": "device",
            "domain": DOMAIN,
            "type": trigger,
            "device_id": device_entry.id,
            "entity_id": entity_entry.id,
            "metadata": {"secondary": True},
        }
        for trigger in toggle_trigger_types
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    expect(triggers == unordered(expected_triggers)).to_be(True)


@test
async def if_fires_on_state_change(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
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

    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {
            const.ATTR_HUMIDITY: 23,
            const.ATTR_CURRENT_HUMIDITY: 35,
            ATTR_MODE: "home",
            const.ATTR_AVAILABLE_MODES: ["home", "away"],
            ATTR_SUPPORTED_FEATURES: 1,
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
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "target_humidity_changed",
                            "below": 20,
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "target_humidity_changed_below"},
                        },
                    },
                    {
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "target_humidity_changed",
                            "above": 30,
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "target_humidity_changed_above"},
                        },
                    },
                    {
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "target_humidity_changed",
                            "above": 30,
                            "for": {"seconds": 5},
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": "target_humidity_changed_above_for"
                            },
                        },
                    },
                    {
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "current_humidity_changed",
                            "below": 30,
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "current_humidity_changed_below"},
                        },
                    },
                    {
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "current_humidity_changed",
                            "above": 40,
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "current_humidity_changed_above"},
                        },
                    },
                    {
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "current_humidity_changed",
                            "above": 40,
                            "for": {"seconds": 5},
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": "current_humidity_changed_above_for"
                            },
                        },
                    },
                    {
                        "trigger": {
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.id,
                            "type": "turned_on",
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
                            "type": "turned_off",
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
                            "type": "changed_states",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {
                                "some": (
                                    "turn_on_or_off {{ trigger.platform }}"
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
    ).to_be(True)

    # Fake that the humidity target is changing
    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {const.ATTR_HUMIDITY: 7, const.ATTR_CURRENT_HUMIDITY: 35},
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("target_humidity_changed_below")

    # Fake that the current humidity is changing
    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {const.ATTR_HUMIDITY: 7, const.ATTR_CURRENT_HUMIDITY: 18},
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(2)
    expect(service_calls[1].data["some"]).to_equal("current_humidity_changed_below")

    # Fake that the humidity target is changing
    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {const.ATTR_HUMIDITY: 37, const.ATTR_CURRENT_HUMIDITY: 18},
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(3)
    expect(service_calls[2].data["some"]).to_equal("target_humidity_changed_above")

    # Fake that the current humidity is changing
    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {const.ATTR_HUMIDITY: 37, const.ATTR_CURRENT_HUMIDITY: 41},
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(4)
    expect(service_calls[3].data["some"]).to_equal("current_humidity_changed_above")

    # Wait 6 minutes
    async_fire_time_changed(hass, dt_util.utcnow() + datetime.timedelta(minutes=6))
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(6)
    expect(
        {service_calls[4].data["some"], service_calls[5].data["some"]}
        == {
            "current_humidity_changed_above_for",
            "target_humidity_changed_above_for",
        }
    ).to_be(True)

    # Fake turn off
    hass.states.async_set(
        entry.entity_id,
        STATE_OFF,
        {const.ATTR_HUMIDITY: 37, const.ATTR_CURRENT_HUMIDITY: 41},
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(8)
    expect(
        {service_calls[6].data["some"], service_calls[7].data["some"]}
        == {
            "turn_off device - humidifier.test_5678 - on - off - None",
            "turn_on_or_off device - humidifier.test_5678 - on - off - None",
        }
    ).to_be(True)

    # Fake turn on
    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {const.ATTR_HUMIDITY: 37, const.ATTR_CURRENT_HUMIDITY: 41},
    )
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(10)
    expect(
        {service_calls[8].data["some"], service_calls[9].data["some"]}
        == {
            "turn_on device - humidifier.test_5678 - off - on - None",
            "turn_on_or_off device - humidifier.test_5678 - off - on - None",
        }
    ).to_be(True)


@test
async def if_fires_on_state_change_legacy(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
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

    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {
            const.ATTR_HUMIDITY: 23,
            ATTR_MODE: "home",
            const.ATTR_AVAILABLE_MODES: ["home", "away"],
            ATTR_SUPPORTED_FEATURES: 1,
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
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": device_entry.id,
                            "entity_id": entry.entity_id,
                            "type": "target_humidity_changed",
                            "below": 20,
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "target_humidity_changed_below"},
                        },
                    },
                ]
            },
        )
    ).to_be(True)

    # Fake that the humidity is changing
    hass.states.async_set(entry.entity_id, STATE_ON, {const.ATTR_HUMIDITY: 7})
    await hass.async_block_till_done()
    expect(len(service_calls)).to_equal(1)
    expect(service_calls[0].data["some"]).to_equal("target_humidity_changed_below")


@test
async def invalid_config(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
) -> None:
    """Test for turn_on and turn_off triggers firing."""
    entry = entity_registry.async_get_or_create(DOMAIN, "test", "5678")

    hass.states.async_set(
        entry.entity_id,
        STATE_ON,
        {
            const.ATTR_HUMIDITY: 23,
            ATTR_MODE: "home",
            const.ATTR_AVAILABLE_MODES: ["home", "away"],
            ATTR_SUPPORTED_FEATURES: 1,
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
                            "platform": "device",
                            "domain": DOMAIN,
                            "device_id": "",
                            "entity_id": entry.id,
                            "type": "target_humidity_changed",
                            "below": 20,
                            "invalid": "invalid",
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "target_humidity_changed"},
                        },
                    },
                ]
            },
        )
    ).to_be(True)

    # Fake that the humidity is changing
    hass.states.async_set(entry.entity_id, STATE_ON, {const.ATTR_HUMIDITY: 7})
    await hass.async_block_till_done()
    # Should not trigger for invalid config
    expect(len(service_calls)).to_equal(0)


@test
async def get_trigger_capabilities_on(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the expected capabilities from a humidifier trigger."""
    capabilities = await device_trigger.async_get_trigger_capabilities(
        hass,
        {
            "platform": "device",
            "domain": "humidifier",
            "type": "turned_on",
            "entity_id": "01234568901234568901234568901",
            "above": "23",
        },
    )

    expect(capabilities and "extra_fields" in capabilities).to_be(True)

    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
        == [
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ]
    ).to_be(True)


@test
async def get_trigger_capabilities_off(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the expected capabilities from a humidifier trigger."""
    capabilities = await device_trigger.async_get_trigger_capabilities(
        hass,
        {
            "platform": "device",
            "domain": "humidifier",
            "type": "turned_off",
            "entity_id": "01234568901234568901234568901",
            "above": "23",
        },
    )

    expect(capabilities and "extra_fields" in capabilities).to_be(True)

    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
        == [
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            }
        ]
    ).to_be(True)


@test
async def get_trigger_capabilities_humidity(
    _t: int = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we get the expected capabilities from a humidifier trigger."""
    capabilities = await device_trigger.async_get_trigger_capabilities(
        hass,
        {
            "platform": "device",
            "domain": "humidifier",
            "type": "target_humidity_changed",
            "entity_id": "01234568901234568901234568901",
            "above": "23",
        },
    )

    expect(capabilities and "extra_fields" in capabilities).to_be(True)

    expect(
        voluptuous_serialize.convert(
            capabilities["extra_fields"], custom_serializer=cv.custom_serializer
        )
        == [
            {
                "description": {"suffix": "%"},
                "name": "above",
                "optional": True,
                "required": False,
                "type": "integer",
            },
            {
                "description": {"suffix": "%"},
                "name": "below",
                "optional": True,
                "required": False,
                "type": "integer",
            },
            {
                "name": "for",
                "optional": True,
                "required": False,
                "type": "positive_time_period_dict",
            },
        ]
    ).to_be(True)
