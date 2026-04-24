"""Test config flow."""

from __future__ import annotations

import json
import time
from unittest.mock import patch

from qbusmqttapi.discovery import QbusDiscovery
from tryke import Depends, expect, fixture, test

from homeassistant.components.qbus.const import CONF_SERIAL_NUMBER, DOMAIN
from homeassistant.components.qbus.coordinator import QbusConfigCoordinator
from homeassistant.config_entries import SOURCE_MQTT, SOURCE_USER
from homeassistant.const import CONF_ID
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo
from homeassistant.util.json import JsonObjectType

from ._fixtures import payload_config as payload_config_fx

from .const import TOPIC_CONFIG

from tests.hass_fixtures import hass as hass_fixture, mock_network

_PAYLOAD_DEVICE_STATE = '{"id":"UL1","properties":{"connected":true},"type":"event"}'


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def step_discovery_confirm_create_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    payload_config: JsonObjectType = Depends(payload_config_fx),
) -> None:
    """Test mqtt confirm step and entry creation."""
    discovery = MqttServiceInfo(
        subscribed_topic="cloudapp/QBUSMQTTGW/+/state",
        topic="cloudapp/QBUSMQTTGW/UL1/state",
        payload=_PAYLOAD_DEVICE_STATE,
        qos=0,
        retain=False,
        timestamp=time.time(),
    )

    with patch.object(
        QbusConfigCoordinator,
        "async_get_or_request_config",
        return_value=QbusDiscovery(payload_config),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_MQTT}, data=discovery
        )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    await hass.async_block_till_done()

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("data")).to_equal(
        {
            CONF_ID: "UL1",
            CONF_SERIAL_NUMBER: "000001",
        }
    )
    expect(result.get("result").unique_id).to_equal("000001")


@test.cases(
    test.case("empty_payload", topic="cloudapp/QBUSMQTTGW/state", payload=b""),
    test.case("invalid_topic", topic="invalid/topic", payload=b"{}"),
)
async def step_mqtt_invalid(
    topic: str,
    payload: bytes,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test mqtt discovery with empty payload."""
    discovery = MqttServiceInfo(
        subscribed_topic=topic,
        topic=topic,
        payload=payload,
        qos=0,
        retain=False,
        timestamp=time.time(),
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_MQTT}, data=discovery
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("invalid_discovery_info")


@test.cases(
    test.case("online_true", payload='{ "online": true }', mqtt_publish=True),
    test.case("online_false", payload='{ "online": false }', mqtt_publish=False),
)
async def handle_gateway_topic_when_online(
    payload: str,
    mqtt_publish: bool,
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test handling of gateway topic with payload indicating online."""
    discovery = MqttServiceInfo(
        subscribed_topic="cloudapp/QBUSMQTTGW/state",
        topic="cloudapp/QBUSMQTTGW/state",
        payload=payload,
        qos=0,
        retain=False,
        timestamp=time.time(),
    )

    with patch("homeassistant.components.mqtt.client.async_publish") as mock_publish:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_MQTT}, data=discovery
        )

    expect(mock_publish.called).to_be(mqtt_publish)
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("discovery_in_progress")


@test
async def handle_config_topic(
    hass: HomeAssistant = Depends(hass_fixture),
    payload_config: JsonObjectType = Depends(payload_config_fx),
) -> None:
    """Test handling of config topic."""
    discovery = MqttServiceInfo(
        subscribed_topic=TOPIC_CONFIG,
        topic=TOPIC_CONFIG,
        payload=json.dumps(payload_config),
        qos=0,
        retain=False,
        timestamp=time.time(),
    )

    with patch("homeassistant.components.mqtt.client.async_publish") as mock_publish:
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_MQTT}, data=discovery
        )

    expect(bool(mock_publish.called)).to_be(True)
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("discovery_in_progress")


@test
async def handle_device_topic_missing_config(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test handling of device topic when config is missing."""
    discovery = MqttServiceInfo(
        subscribed_topic="cloudapp/QBUSMQTTGW/+/state",
        topic="cloudapp/QBUSMQTTGW/UL1/state",
        payload=_PAYLOAD_DEVICE_STATE,
        qos=0,
        retain=False,
        timestamp=time.time(),
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_MQTT}, data=discovery
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("invalid_discovery_info")


@test
async def handle_device_topic_device_not_found(
    hass: HomeAssistant = Depends(hass_fixture),
    payload_config: JsonObjectType = Depends(payload_config_fx),
) -> None:
    """Test handling of device topic when device is not found."""
    discovery = MqttServiceInfo(
        subscribed_topic="cloudapp/QBUSMQTTGW/+/state",
        topic="cloudapp/QBUSMQTTGW/UL2/state",
        payload='{"id":"UL2","properties":{"connected":true},"type":"event"}',
        qos=0,
        retain=False,
        timestamp=time.time(),
    )

    with patch.object(
        QbusConfigCoordinator,
        "async_get_or_request_config",
        return_value=QbusDiscovery(payload_config),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_MQTT}, data=discovery
        )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("invalid_discovery_info")


@test
async def step_user_not_supported(
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test user step, which should abort."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("not_supported")
