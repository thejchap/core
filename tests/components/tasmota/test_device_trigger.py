"""The tests for Tasmota device triggers."""

import copy
import json
from typing import Any
from unittest.mock import Mock, patch

from hatasmota.switch import TasmotaSwitchTriggerConfig
from pytest_unordered import unordered
from tryke import Depends, fixture, test

from homeassistant.components import automation
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.tasmota import _LOGGER
from homeassistant.components.tasmota.const import DEFAULT_PREFIX, DOMAIN
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.trigger import async_initialize_triggers
from homeassistant.setup import async_setup_component

from ._fixtures import (
    mqtt_mock as mqtt_mock_fixture,
    setup_tasmota as setup_tasmota_fixture,
)
from .test_common import DEFAULT_CONFIG, remove_device

from tests.common import async_fire_mqtt_message, async_get_device_automations
from tests.components.mqtt._fixtures import service_calls as service_calls_fixture
from tests.hass_fixtures import (
    device_registry as device_registry_fixture,
    hass as hass_fixture,
    hass_ws_client as hass_ws_client_fixture,
    mock_network,
)
from tests.typing import WebSocketGenerator


@fixture
async def _trigger_executor(
    _network: None = Depends(mock_network),
    hass: HomeAssistant = Depends(hass_fixture),
) -> HomeAssistant:
    """Anchor fixture for tryke Depends() resolution."""
    return hass


@test
async def get_triggers_btn(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test we get the expected triggers from a discovered mqtt device."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["btn"][0] = 1
    config["btn"][1] = 1
    config["so"]["13"] = 1
    config["so"]["73"] = 1
    mac = config["mac"]

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "discovery_id": "00000049A3BC_button_1_SINGLE",
            "type": "button_short_press",
            "subtype": "button_1",
            "metadata": {},
        },
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "discovery_id": "00000049A3BC_button_2_SINGLE",
            "type": "button_short_press",
            "subtype": "button_2",
            "metadata": {},
        },
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert triggers == unordered(expected_triggers)


@test
async def get_triggers_swc(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test we get the expected triggers from a discovered mqtt device."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = 0
    mac = config["mac"]

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "discovery_id": "00000049A3BC_switch_1_TOGGLE",
            "type": "button_short_press",
            "subtype": "switch_1",
            "metadata": {},
        },
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert triggers == unordered(expected_triggers)


@test
async def get_unknown_triggers(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test we don't get unknown triggers."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = -1
    mac = config["mac"]

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_switch_0_2",
                        "type": "button_short_press",
                        "subtype": "button_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
            ]
        },
    )

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert triggers == []


@test
async def get_non_existing_triggers(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test getting non existing triggers."""
    config1 = copy.deepcopy(DEFAULT_CONFIG)
    config1["swc"][0] = -1
    mac = config1["mac"]

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config1))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert triggers == []


@test
async def discover_bad_triggers(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test exception handling when discovering trigger."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = 0
    mac = config["mac"]

    with patch(
        "hatasmota.discovery.get_switch_triggers",
        return_value=[object()],
    ):
        async_fire_mqtt_message(
            hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config)
        )
        await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert triggers == []

    class FakeTrigger(TasmotaSwitchTriggerConfig):
        """Bad TasmotaSwitchTriggerConfig to cause exceptions."""

        @property
        def is_active(self):
            return True

    with patch(
        "hatasmota.discovery.get_switch_triggers",
        return_value=[
            FakeTrigger(
                event=None,
                idx=1,
                mac=None,
                source=None,
                subtype=None,
                switchname=None,
                trigger_topic=None,
                type=None,
            )
        ],
    ):
        async_fire_mqtt_message(
            hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config)
        )
        await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert triggers == []

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()

    expected_triggers = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "discovery_id": "00000049A3BC_switch_1_TOGGLE",
            "type": "button_short_press",
            "subtype": "switch_1",
            "metadata": {},
        },
    ]
    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert triggers == unordered(expected_triggers)


@test
async def update_remove_triggers(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test triggers can be updated and removed."""
    config1 = copy.deepcopy(DEFAULT_CONFIG)
    config1["swc"][0] = 5
    mac = config1["mac"]

    config2 = copy.deepcopy(DEFAULT_CONFIG)
    config2["swc"][0] = 8

    config3 = copy.deepcopy(DEFAULT_CONFIG)
    config3["swc"][0] = -1

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config1))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    expected_triggers1 = [
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "discovery_id": "00000049A3BC_switch_1_TOGGLE",
            "type": "button_short_press",
            "subtype": "switch_1",
            "metadata": {},
        },
        {
            "platform": "device",
            "domain": DOMAIN,
            "device_id": device_entry.id,
            "discovery_id": "00000049A3BC_switch_1_HOLD",
            "type": "button_long_press",
            "subtype": "switch_1",
            "metadata": {},
        },
    ]
    expected_triggers2 = copy.deepcopy(expected_triggers1)
    expected_triggers2[1]["type"] = "button_double_press"

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    for expected in expected_triggers1:
        assert expected in triggers

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config2))
    await hass.async_block_till_done()

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    for expected in expected_triggers2:
        assert expected in triggers

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config3))
    await hass.async_block_till_done()

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device_entry.id
    )
    assert triggers == []


@test
async def if_fires_on_mqtt_message_btn(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test button triggers firing."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["btn"][0] = 1
    config["btn"][2] = 1
    config["so"]["73"] = 1
    mac = config["mac"]

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_button_1_SINGLE",
                        "type": "button_short_press",
                        "subtype": "button_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press_1")},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_button_3_SINGLE",
                        "subtype": "button_3",
                        "type": "button_short_press",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press_3")},
                    },
                },
            ]
        },
    )

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Button1":{"Action":"SINGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "short_press_1"

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Button3":{"Action":"SINGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "short_press_3"


@test
async def if_fires_on_mqtt_message_swc(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test switch triggers firing."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = 0
    config["swc"][1] = 0
    config["swc"][2] = 9
    config["swn"][2] = "custom_switch"
    mac = config["mac"]

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()
    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                        "type": "button_short_press",
                        "subtype": "switch_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press_1")},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_switch_2_TOGGLE",
                        "type": "button_short_press",
                        "subtype": "switch_2",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press_2")},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_switch_3_HOLD",
                        "subtype": "switch_3",
                        "type": "button_double_press",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("long_press_3")},
                    },
                },
            ]
        },
    )

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "short_press_1"

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch2":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "short_press_2"

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"custom_switch":{"Action":"HOLD"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 3
    assert service_calls[2].data["some"] == "long_press_3"


@test
async def if_fires_on_mqtt_message_late_discover(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test triggers firing of MQTT device triggers discovered after setup."""
    config1 = copy.deepcopy(DEFAULT_CONFIG)
    config1["swc"][0] = -1
    mac = config1["mac"]

    config2 = copy.deepcopy(DEFAULT_CONFIG)
    config2["swc"][0] = 0
    config2["swc"][3] = 9
    config2["swn"][3] = "custom_switch"

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config1))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                        "type": "button_short_press",
                        "subtype": "switch_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_switch_4_HOLD",
                        "type": "switch_4",
                        "subtype": "button_double_press",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("double_press")},
                    },
                },
            ]
        },
    )

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config2))
    await hass.async_block_till_done()

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0].data["some"] == "short_press"

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"custom_switch":{"Action":"HOLD"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 2
    assert service_calls[1].data["some"] == "double_press"


@test
async def if_fires_on_mqtt_message_after_update(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test triggers firing after update."""
    config1 = copy.deepcopy(DEFAULT_CONFIG)
    config2 = copy.deepcopy(DEFAULT_CONFIG)
    config1["swc"][0] = 0
    config2["swc"][0] = 0
    config2["tp"][1] = "status"
    mac = config1["mac"]

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config1))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                        "type": "button_short_press",
                        "subtype": "switch_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
            ]
        },
    )

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config2))
    await hass.async_block_till_done()

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/status/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 2

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config2))
    await hass.async_block_till_done()

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 2

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/status/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 3


@test
async def no_resubscribe_same_topic(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test subscription to topics without change."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = 0
    mac = config["mac"]

    mqtt_mock.async_subscribe.reset_mock()

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                        "type": "button_short_press",
                        "subtype": "switch_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
            ]
        },
    )

    call_count = mqtt_mock.async_subscribe.call_count
    assert call_count == 1
    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()
    assert mqtt_mock.async_subscribe.call_count == call_count


@test
async def not_fires_on_mqtt_message_after_remove_by_mqtt(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test triggers not firing after removal."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = 0
    mac = config["mac"]

    mqtt_mock.async_subscribe.reset_mock()

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                        "type": "button_short_press",
                        "subtype": "switch_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
            ]
        },
    )

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1

    config["swc"][0] = -1
    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1

    config["swc"][0] = 0
    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 2


@test
async def not_fires_on_mqtt_message_after_remove_from_registry(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    service_calls: list[ServiceCall] = Depends(service_calls_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test triggers not firing after removal."""
    assert await async_setup_component(hass, "config", {})
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = 0
    mac = config["mac"]

    mqtt_mock.async_subscribe.reset_mock()

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: [
                {
                    "trigger": {
                        "platform": "device",
                        "domain": DOMAIN,
                        "device_id": device_entry.id,
                        "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                        "type": "button_short_press",
                        "subtype": "switch_1",
                    },
                    "action": {
                        "service": "test.automation",
                        "data_template": {"some": ("short_press")},
                    },
                },
            ]
        },
    )

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1

    await remove_device(hass, hass_ws_client, device_entry.id)
    await hass.async_block_till_done()

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1


@test
async def attach_remove(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test attach and removal of trigger."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = 0
    mac = config["mac"]

    mqtt_mock.async_subscribe.reset_mock()

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    service_calls: list[str] = []

    def callback(trigger, context):
        service_calls.append(trigger["trigger"]["description"])

    remove = await async_initialize_triggers(
        hass,
        [
            {
                "platform": "device",
                "domain": DOMAIN,
                "device_id": device_entry.id,
                "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                "type": "button_short_press",
                "subtype": "switch_1",
            },
        ],
        callback,
        DOMAIN,
        "mock-name",
        _LOGGER.log,
    )

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0] == "event 'tasmota_event'"

    remove()
    await hass.async_block_till_done()

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1


@test
async def attach_remove_late(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test attach and removal of trigger."""
    config1 = copy.deepcopy(DEFAULT_CONFIG)
    config1["swc"][0] = -1
    mac = config1["mac"]

    config2 = copy.deepcopy(DEFAULT_CONFIG)
    config2["swc"][0] = 0

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config1))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    service_calls: list[str] = []

    def callback(trigger, context):
        service_calls.append(trigger["trigger"]["description"])

    remove = await async_initialize_triggers(
        hass,
        [
            {
                "platform": "device",
                "domain": DOMAIN,
                "device_id": device_entry.id,
                "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                "type": "button_short_press",
                "subtype": "switch_1",
            },
        ],
        callback,
        DOMAIN,
        "mock-name",
        _LOGGER.log,
    )

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 0

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config2))
    await hass.async_block_till_done()

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0] == "event 'tasmota_event'"

    remove()
    await hass.async_block_till_done()

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1


@test
async def attach_remove_late2(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test attach and removal of trigger."""
    config1 = copy.deepcopy(DEFAULT_CONFIG)
    config1["swc"][0] = -1
    mac = config1["mac"]

    config2 = copy.deepcopy(DEFAULT_CONFIG)
    config2["swc"][0] = 0

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config1))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    service_calls: list[str] = []

    def callback(trigger, context):
        service_calls.append(trigger["trigger"]["description"])

    remove = await async_initialize_triggers(
        hass,
        [
            {
                "platform": "device",
                "domain": DOMAIN,
                "device_id": device_entry.id,
                "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                "type": "button_short_press",
                "subtype": "switch_1",
            },
        ],
        callback,
        DOMAIN,
        "mock-name",
        _LOGGER.log,
    )

    remove()
    await hass.async_block_till_done()

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config1))
    await hass.async_block_till_done()

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 0


@test
async def attach_remove_unknown1(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test attach and removal of unknown trigger."""
    config1 = copy.deepcopy(DEFAULT_CONFIG)
    config1["swc"][0] = -1
    mac = config1["mac"]

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config1))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    remove = await async_initialize_triggers(
        hass,
        [
            {
                "platform": "device",
                "domain": DOMAIN,
                "device_id": device_entry.id,
                "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                "type": "button_short_press",
                "subtype": "switch_1",
            },
        ],
        Mock(),
        DOMAIN,
        "mock-name",
        _LOGGER.log,
    )

    remove()
    await hass.async_block_till_done()


@test
async def attach_unknown_remove_device_from_registry(
    hass: HomeAssistant = Depends(_trigger_executor),
    hass_ws_client: WebSocketGenerator = Depends(hass_ws_client_fixture),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test attach and removal of device with unknown trigger."""
    assert await async_setup_component(hass, "config", {})
    config1 = copy.deepcopy(DEFAULT_CONFIG)
    config1["swc"][0] = -1
    mac = config1["mac"]

    config2 = copy.deepcopy(DEFAULT_CONFIG)
    config2["swc"][0] = 0

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config2))
    await hass.async_block_till_done()

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config1))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    await async_initialize_triggers(
        hass,
        [
            {
                "platform": "device",
                "domain": DOMAIN,
                "device_id": device_entry.id,
                "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                "type": "button_short_press",
                "subtype": "switch_1",
            },
        ],
        Mock(),
        DOMAIN,
        "mock-name",
        _LOGGER.log,
    )

    await remove_device(hass, hass_ws_client, device_entry.id)
    await hass.async_block_till_done()


@test
async def attach_remove_config_entry(
    hass: HomeAssistant = Depends(_trigger_executor),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
    _setup: None = Depends(setup_tasmota_fixture),
) -> None:
    """Test trigger cleanup when removing a Tasmota config entry."""
    config = copy.deepcopy(DEFAULT_CONFIG)
    config["swc"][0] = 0
    mac = config["mac"]

    mqtt_mock.async_subscribe.reset_mock()

    async_fire_mqtt_message(hass, f"{DEFAULT_PREFIX}/{mac}/config", json.dumps(config))
    await hass.async_block_till_done()

    device_entry = device_registry.async_get_device(
        connections={(dr.CONNECTION_NETWORK_MAC, mac)}
    )

    service_calls: list[str] = []

    def callback(trigger, context):
        service_calls.append(trigger["trigger"]["description"])

    await async_initialize_triggers(
        hass,
        [
            {
                "platform": "device",
                "domain": DOMAIN,
                "device_id": device_entry.id,
                "discovery_id": "00000049A3BC_switch_1_TOGGLE",
                "type": "button_short_press",
                "subtype": "switch_1",
            },
        ],
        callback,
        DOMAIN,
        "mock-name",
        _LOGGER.log,
    )

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1
    assert service_calls[0] == "event 'tasmota_event'"

    config_entries = hass.config_entries.async_entries("tasmota")
    await hass.config_entries.async_remove(config_entries[0].entry_id)
    await hass.async_block_till_done()

    async_fire_mqtt_message(
        hass, "tasmota_49A3BC/stat/RESULT", '{"Switch1":{"Action":"TOGGLE"}}'
    )
    await hass.async_block_till_done()
    assert len(service_calls) == 1
