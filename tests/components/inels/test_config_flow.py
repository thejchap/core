"""Test the iNELS config flow."""

from typing import Any
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.inels.const import DOMAIN, TITLE
from homeassistant.components.mqtt import MQTT_CONNECTION_STATE
from homeassistant.config_entries import SOURCE_MQTT, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.helpers.service_info.mqtt import MqttServiceInfo

from tests.common import MockConfigEntry
from tests.components.inels._fixtures import mqtt_mock as mqtt_mock_fixture
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def mqtt_config_single_instance(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """The MQTT test flow is aborted if an entry already exists."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_MQTT}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def mqtt_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """When an MQTT message is received on the discovery topic, it triggers a config flow."""
    discovery_info = MqttServiceInfo(
        topic="inels/status/MAC_ADDRESS/gw",
        payload='{"CUType":"CU3-08M","Status":"Runfast","FW":"02.97.18"}',
        qos=0,
        retain=False,
        subscribed_topic="inels/status/#",
        timestamp=None,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_MQTT}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    with patch(
        "homeassistant.components.inels.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TITLE)
    expect(result["result"].data).to_equal({})
    mock_setup_entry.assert_called_once()


@test
async def mqtt_abort_invalid_topic(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Check MQTT flow aborts if discovery topic is invalid."""
    discovery_info = MqttServiceInfo(
        topic="inels/status/MAC_ADDRESS/wrong_topic",
        payload='{"CUType":"CU3-08M","Status":"Runfast","FW":"02.97.18"}',
        qos=0,
        retain=False,
        subscribed_topic="inels/status/#",
        timestamp=None,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_MQTT}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_discovery_info")


@test
async def mqtt_abort_empty_payload(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Check MQTT flow aborts if discovery payload is empty."""
    discovery_info = MqttServiceInfo(
        topic="inels/status/MAC_ADDRESS/gw",
        payload="",
        qos=0,
        retain=False,
        subscribed_topic="inels/status/#",
        timestamp=None,
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_MQTT}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("invalid_discovery_info")


@test
async def mqtt_abort_already_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test that a second MQTT flow is aborted when one is already in progress."""
    discovery_info = MqttServiceInfo(
        topic="inels/status/MAC_ADDRESS/gw",
        payload='{"CUType":"CU3-08M","Status":"Runfast","FW":"02.97.18"}',
        qos=0,
        retain=False,
        subscribed_topic="inels/status/#",
        timestamp=None,
    )

    # Start first MQTT flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_MQTT}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    # Try to start second MQTT flow while first is in progress
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_MQTT}, data=discovery_info
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test
async def user_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """Test if the user can finish a config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    with patch(
        "homeassistant.components.inels.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TITLE)
    expect(result["result"].data).to_equal({})
    mock_setup_entry.assert_called_once()


@test
async def user_config_single_instance(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """The user test flow is aborted if an entry already exists."""
    MockConfigEntry(domain=DOMAIN).add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("single_instance_allowed")


@test
async def user_setup_mqtt_not_connected(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    mqtt_mock: Any = Depends(mqtt_mock_fixture),
) -> None:
    """The user setup test flow is aborted when MQTT is not connected."""
    mqtt_mock.connected = False
    async_dispatcher_send(hass, MQTT_CONNECTION_STATE, False)
    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("mqtt_not_connected")


@test
async def user_setup_mqtt_not_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """The user setup test flow is aborted when MQTT is not configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("mqtt_not_configured")
