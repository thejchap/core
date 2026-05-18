"""deCONZ device automation tests (tryke port)."""

from __future__ import annotations

from collections.abc import Callable, Generator
import logging
from typing import Any
from unittest.mock import Mock, patch

from pytest_unordered import unordered
from tryke import Depends, expect, fixture, test

from homeassistant.components.automation import DOMAIN as AUTOMATION_DOMAIN
from homeassistant.components.binary_sensor import DOMAIN as BINARY_SENSOR_DOMAIN

# pylint: disable-next=hass-component-root-import
from homeassistant.components.binary_sensor.device_trigger import (
    CONF_BAT_LOW,
    CONF_NOT_BAT_LOW,
    CONF_NOT_TAMPERED,
    CONF_TAMPERED,
)
from homeassistant.components.deconz import device_trigger
from homeassistant.components.deconz.const import DOMAIN
from homeassistant.components.deconz.device_trigger import CONF_SUBTYPE
from homeassistant.components.device_automation import DeviceAutomationType
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import (
    ATTR_BATTERY_LEVEL,
    ATTR_ENTITY_ID,
    CONF_DEVICE_ID,
    CONF_DOMAIN,
    CONF_PLATFORM,
    CONF_TYPE,
    STATE_UNAVAILABLE,
)
from homeassistant.core import (
    Context,
    HomeAssistant,
    ServiceCall,
    ServiceResponse,
)
from homeassistant.exceptions import ServiceNotFound
from homeassistant.helpers import device_registry as dr, entity_registry as er
from homeassistant.helpers.trigger import async_initialize_triggers
from homeassistant.setup import async_setup_component

from tests.common import async_get_device_automations
from tests.components.deconz._fixtures import (
    mock_websocket as mock_websocket_fixture,
    setup_deconz,
)
from tests.hass_fixtures import (
    aioclient_mock,
    device_registry as device_registry_fixture,
    entity_registry as entity_registry_fixture,
    hass as hass_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

_LOGGER = logging.getLogger(__name__)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> int:
    """Anchor fixture for tryke fixture-injection."""
    return 0


@fixture
def service_calls(
    hass: HomeAssistant = Depends(hass_fixture),
) -> Generator[list[ServiceCall]]:
    """Track all service calls."""
    calls: list[ServiceCall] = []

    _original_async_call = hass.services.async_call

    async def _async_call(
        self,
        domain: str,
        service: str,
        service_data: dict[str, Any] | None = None,
        blocking: bool = False,
        context: Context | None = None,
        target: dict[str, Any] | None = None,
        return_response: bool = False,
    ) -> ServiceResponse:
        calls.append(
            ServiceCall(hass, domain, service, service_data, context, return_response)
        )
        try:
            return await _original_async_call(
                domain,
                service,
                service_data,
                blocking,
                context,
                target,
                return_response,
            )
        except ServiceNotFound:
            _LOGGER.debug("Ignoring unknown service call to %s.%s", domain, service)
        return None

    with patch("homeassistant.core.ServiceRegistry.async_call", _async_call):
        yield calls


@fixture
def sensor_ws_data(
    mock_websocket: Any = Depends(mock_websocket_fixture),
) -> Callable[[dict[str, Any]], Any]:
    """Return a callable that sends sensor websocket events."""

    async def send(data: dict[str, Any]) -> None:
        payload: dict[str, Any] = {"r": "sensors"}
        payload.update(data)
        payload.setdefault("t", "event")
        payload.setdefault("e", "changed")
        payload.setdefault("id", "0")
        await mock_websocket(data=payload)

    return send


TRADFRI_SWITCH_SENSOR = {
    "config": {
        "alert": "none",
        "battery": 60,
        "group": "10",
        "on": True,
        "reachable": True,
    },
    "ep": 1,
    "etag": "1b355c0b6d2af28febd7ca9165881952",
    "manufacturername": "IKEA of Sweden",
    "mode": 1,
    "modelid": "TRADFRI on/off switch",
    "name": "TRÅDFRI on/off switch ",
    "state": {"buttonevent": 2002, "lastupdated": "2019-09-07T07:39:39"},
    "swversion": "1.4.018",
    "type": "ZHASwitch",
    "uniqueid": "d0:cf:5e:ff:fe:71:a4:3a-01-1000",
}

KEYPAD_SENSOR = {
    "config": {
        "battery": 95,
        "enrolled": 1,
        "on": True,
        "pending": [],
        "reachable": True,
    },
    "ep": 1,
    "etag": "5aaa1c6bae8501f59929539c6e8f44d6",
    "lastseen": "2021-07-25T18:07Z",
    "manufacturername": "lk",
    "modelid": "ZB-KeypadGeneric-D0002",
    "name": "Keypad",
    "state": {
        "action": "armed_stay",
        "lastupdated": "2021-07-25T18:02:51.172",
        "lowbattery": False,
        "panel": "exit_delay",
        "seconds_remaining": 55,
        "tampered": False,
    },
    "swversion": "3.13",
    "type": "ZHAAncillaryControl",
    "uniqueid": "00:00:00:00:00:00:00:00-00",
}

UNSUPPORTED_REMOTE_SENSOR = {
    "config": {
        "alert": "none",
        "group": "10",
        "on": True,
        "reachable": True,
    },
    "ep": 1,
    "etag": "1b355c0b6d2af28febd7ca9165881952",
    "manufacturername": "IKEA of Sweden",
    "mode": 1,
    "modelid": "Unsupported model",
    "name": "TRÅDFRI on/off switch ",
    "state": {"buttonevent": 2002, "lastupdated": "2019-09-07T07:39:39"},
    "swversion": "1.4.018",
    "type": "ZHASwitch",
    "uniqueid": "d0:cf:5e:ff:fe:71:a4:3a-01-1000",
}


@test
async def get_triggers(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test triggers work."""
    await setup_deconz(hass, aioclient, sensor_payload=TRADFRI_SWITCH_SENSOR)

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "d0:cf:5e:ff:fe:71:a4:3a")}
    )
    battery_sensor_entry = entity_registry.async_get(
        "sensor.tradfri_on_off_switch_battery"
    )

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device.id
    )

    expected_triggers = [
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
            CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
            "metadata": {},
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_LONG_PRESS,
            CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
            "metadata": {},
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_LONG_RELEASE,
            CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
            "metadata": {},
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
            CONF_SUBTYPE: device_trigger.CONF_TURN_OFF,
            "metadata": {},
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_LONG_PRESS,
            CONF_SUBTYPE: device_trigger.CONF_TURN_OFF,
            "metadata": {},
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: DOMAIN,
            CONF_PLATFORM: "device",
            CONF_TYPE: device_trigger.CONF_LONG_RELEASE,
            CONF_SUBTYPE: device_trigger.CONF_TURN_OFF,
            "metadata": {},
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: SENSOR_DOMAIN,
            ATTR_ENTITY_ID: battery_sensor_entry.id,
            CONF_PLATFORM: "device",
            CONF_TYPE: ATTR_BATTERY_LEVEL,
            "metadata": {"secondary": True},
        },
    ]

    expect(triggers).to_equal(unordered(expected_triggers))


@test
async def get_triggers_for_alarm_event(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    entity_registry: er.EntityRegistry = Depends(entity_registry_fixture),
) -> None:
    """Test triggers work."""
    await setup_deconz(hass, aioclient, sensor_payload=KEYPAD_SENSOR)

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "00:00:00:00:00:00:00:00")}
    )
    bat_entity = entity_registry.async_get("sensor.keypad_battery")
    low_bat_entity = entity_registry.async_get("binary_sensor.keypad_low_battery")
    tamper_entity = entity_registry.async_get("binary_sensor.keypad_tampered")

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device.id
    )

    expected_triggers = [
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: BINARY_SENSOR_DOMAIN,
            ATTR_ENTITY_ID: low_bat_entity.id,
            CONF_PLATFORM: "device",
            CONF_TYPE: CONF_BAT_LOW,
            "metadata": {"secondary": True},
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: BINARY_SENSOR_DOMAIN,
            ATTR_ENTITY_ID: low_bat_entity.id,
            CONF_PLATFORM: "device",
            CONF_TYPE: CONF_NOT_BAT_LOW,
            "metadata": {"secondary": True},
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: BINARY_SENSOR_DOMAIN,
            ATTR_ENTITY_ID: tamper_entity.id,
            CONF_PLATFORM: "device",
            CONF_TYPE: CONF_TAMPERED,
            "metadata": {"secondary": True},
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: BINARY_SENSOR_DOMAIN,
            ATTR_ENTITY_ID: tamper_entity.id,
            CONF_PLATFORM: "device",
            CONF_TYPE: CONF_NOT_TAMPERED,
            "metadata": {"secondary": True},
        },
        {
            CONF_DEVICE_ID: device.id,
            CONF_DOMAIN: SENSOR_DOMAIN,
            ATTR_ENTITY_ID: bat_entity.id,
            CONF_PLATFORM: "device",
            CONF_TYPE: ATTR_BATTERY_LEVEL,
            "metadata": {"secondary": True},
        },
    ]

    expect(triggers).to_equal(unordered(expected_triggers))


@test
async def get_triggers_manage_unsupported_remotes(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Verify no triggers for an unsupported remote."""
    await setup_deconz(hass, aioclient, sensor_payload=UNSUPPORTED_REMOTE_SENSOR)

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "d0:cf:5e:ff:fe:71:a4:3a")}
    )

    triggers = await async_get_device_automations(
        hass, DeviceAutomationType.TRIGGER, device.id
    )

    expect(triggers).to_equal(unordered([]))


@test
async def functional_device_trigger(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
    calls: list[ServiceCall] = Depends(service_calls),
    send_sensor: Callable[[dict[str, Any]], Any] = Depends(sensor_ws_data),
) -> None:
    """Test proper matching and attachment of device trigger automation."""
    await setup_deconz(hass, aioclient, sensor_payload=TRADFRI_SWITCH_SENSOR)

    device = device_registry.async_get_device(
        identifiers={(DOMAIN, "d0:cf:5e:ff:fe:71:a4:3a")}
    )

    expect(
        await async_setup_component(
            hass,
            AUTOMATION_DOMAIN,
            {
                AUTOMATION_DOMAIN: [
                    {
                        "trigger": {
                            CONF_PLATFORM: "device",
                            CONF_DOMAIN: DOMAIN,
                            CONF_DEVICE_ID: device.id,
                            CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
                            CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "test_trigger_button_press"},
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()

    expect(len(hass.states.async_entity_ids(AUTOMATION_DOMAIN))).to_be(1)

    await send_sensor({"state": {"buttonevent": 1002}})
    await hass.async_block_till_done()
    expect(len(calls)).to_be(1)
    expect(calls[0].data["some"]).to_be("test_trigger_button_press")


@test.skip("Temporarily disabled until automation validation is improved")
async def validate_trigger_unknown_device() -> None:
    """Test unknown device does not return a trigger config."""


@test
async def validate_trigger_unsupported_device(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test unsupported device doesn't return a trigger config."""
    config_entry_setup = await setup_deconz(hass, aioclient)

    device = device_registry.async_get_or_create(
        config_entry_id=config_entry_setup.entry_id,
        identifiers={(DOMAIN, "d0:cf:5e:ff:fe:71:a4:3a")},
        model="unsupported",
    )

    expect(
        await async_setup_component(
            hass,
            AUTOMATION_DOMAIN,
            {
                AUTOMATION_DOMAIN: [
                    {
                        "trigger": {
                            CONF_PLATFORM: "device",
                            CONF_DOMAIN: DOMAIN,
                            CONF_DEVICE_ID: device.id,
                            CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
                            CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
                        },
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "test_trigger_button_press"},
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    automations = hass.states.async_entity_ids(AUTOMATION_DOMAIN)
    expect(len(automations)).to_be(1)
    expect(hass.states.get(automations[0]).state).to_be(STATE_UNAVAILABLE)


@test
async def validate_trigger_unsupported_trigger(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test unsupported trigger does not return a trigger config."""
    config_entry_setup = await setup_deconz(hass, aioclient)

    device = device_registry.async_get_or_create(
        config_entry_id=config_entry_setup.entry_id,
        identifiers={(DOMAIN, "d0:cf:5e:ff:fe:71:a4:3a")},
        model="TRADFRI on/off switch",
    )

    trigger_config = {
        CONF_PLATFORM: "device",
        CONF_DOMAIN: DOMAIN,
        CONF_DEVICE_ID: device.id,
        CONF_TYPE: "unsupported",
        CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
    }

    expect(
        await async_setup_component(
            hass,
            AUTOMATION_DOMAIN,
            {
                AUTOMATION_DOMAIN: [
                    {
                        "trigger": trigger_config,
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "test_trigger_button_press"},
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    automations = hass.states.async_entity_ids(AUTOMATION_DOMAIN)
    expect(len(automations)).to_be(1)
    expect(hass.states.get(automations[0]).state).to_be(STATE_UNAVAILABLE)


@test
async def attach_trigger_no_matching_event(
    _trigger: int = Depends(_trigger_executor),
    _ws: Any = Depends(mock_websocket_fixture),
    hass: HomeAssistant = Depends(hass_fixture),
    aioclient: AiohttpClientMocker = Depends(aioclient_mock),
    device_registry: dr.DeviceRegistry = Depends(device_registry_fixture),
) -> None:
    """Test no matching event for device doesn't return a trigger config."""
    config_entry_setup = await setup_deconz(hass, aioclient)

    device = device_registry.async_get_or_create(
        config_entry_id=config_entry_setup.entry_id,
        identifiers={(DOMAIN, "d0:cf:5e:ff:fe:71:a4:3a")},
        name="Tradfri switch",
        model="TRADFRI on/off switch",
    )

    trigger_config = {
        CONF_PLATFORM: "device",
        CONF_DOMAIN: DOMAIN,
        CONF_DEVICE_ID: device.id,
        CONF_TYPE: device_trigger.CONF_SHORT_PRESS,
        CONF_SUBTYPE: device_trigger.CONF_TURN_ON,
    }

    expect(
        await async_setup_component(
            hass,
            AUTOMATION_DOMAIN,
            {
                AUTOMATION_DOMAIN: [
                    {
                        "trigger": trigger_config,
                        "action": {
                            "service": "test.automation",
                            "data_template": {"some": "test_trigger_button_press"},
                        },
                    },
                ]
            },
        )
    ).to_be_truthy()
    await hass.async_block_till_done()

    expect(len(hass.states.async_entity_ids(AUTOMATION_DOMAIN))).to_be(1)

    # Assert that deCONZ async_attach_trigger raises InvalidDeviceAutomationConfig
    expect(
        await async_initialize_triggers(
            hass,
            [trigger_config],
            action=Mock(),
            domain=AUTOMATION_DOMAIN,
            name="mock-name",
            log_cb=Mock(),
        )
    ).to_be_falsy()
