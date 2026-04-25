"""Test the Motionblinds config flow."""

import socket
from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.motion_blinds import const
from homeassistant.components.motion_blinds.config_flow import DEFAULT_GATEWAY_NAME
from homeassistant.const import CONF_API_KEY, CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import motion_blinds_connect

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

TEST_HOST = "1.2.3.4"
TEST_HOST2 = "5.6.7.8"
TEST_HOST_HA = "9.10.11.12"
TEST_HOST_ANY = "any"
TEST_API_KEY = "12ab345c-d67e-8f"
TEST_API_KEY2 = "f8e76dc5-43ba-21"
TEST_MAC = "ab:bb:cc:dd:ee:ff"
TEST_MAC2 = "ff:ee:dd:cc:bb:aa"
DHCP_FORMATTED_MAC = "aabbccddeeff"

TEST_DISCOVERY_2 = {
    TEST_HOST: {
        "msgType": "GetDeviceListAck",
        "mac": TEST_MAC,
        "deviceType": "02000002",
        "ProtocolVersion": "0.9",
        "token": "12345A678B9CDEFG",
        "data": [
            {"mac": "abcdefghujkl", "deviceType": "02000002"},
            {"mac": "abcdefghujkl0001", "deviceType": "10000000"},
        ],
    },
    TEST_HOST2: {
        "msgType": "GetDeviceListAck",
        "mac": TEST_MAC2,
        "deviceType": "02000002",
        "ProtocolVersion": "0.9",
        "token": "12345A678B9CDEFG",
        "data": [
            {"mac": "abcdefghujkl", "deviceType": "02000002"},
            {"mac": "abcdefghujkl0001", "deviceType": "10000000"},
        ],
    },
}


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _connect: None = Depends(motion_blinds_connect),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def config_flow_manual_host_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Successful flow manually initialized by the user."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("connect")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: TEST_API_KEY}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_GATEWAY_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_API_KEY: TEST_API_KEY,
            const.CONF_INTERFACE: TEST_HOST_ANY,
        }
    )


@test
async def config_flow_discovery_1_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Successful flow with 1 gateway discovered."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("connect")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.motion_blinds.gateway.AsyncMotionMulticast.Stop_listen",
        side_effect=socket.gaierror,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: TEST_API_KEY}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_GATEWAY_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_API_KEY: TEST_API_KEY,
            const.CONF_INTERFACE: TEST_HOST_ANY,
        }
    )


@test
async def config_flow_discovery_2_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Successful flow with 2 gateway discovered."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.motion_blinds.config_flow.MotionDiscovery.discover",
        return_value=TEST_DISCOVERY_2,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("select")
    expect(result["data_schema"].schema["select_ip"].container).to_equal(
        [TEST_HOST, TEST_HOST2]
    )
    expect(result["errors"]).to_be(None)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"select_ip": TEST_HOST2}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("connect")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.motion_blinds.gateway.MotionGateway.Check_gateway_multicast",
        side_effect=socket.timeout,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: TEST_API_KEY}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_GATEWAY_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST2,
            CONF_API_KEY: TEST_API_KEY,
            const.CONF_INTERFACE: TEST_HOST_ANY,
        }
    )


@test
async def config_flow_connection_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Failed flow manually initialized by the user with connection timeout."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("connect")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.motion_blinds.gateway.MotionGateway.GetDeviceList",
        side_effect=socket.timeout,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: TEST_API_KEY}
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("connection_error")


@test
async def config_flow_discovery_fail(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Failed flow with no gateways discovered."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.motion_blinds.config_flow.MotionDiscovery.discover",
        return_value={},
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "discovery_error"})


@test
async def config_flow_invalid_interface(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Failed flow manually initialized by the user with invalid interface."""
    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("connect")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.motion_blinds.gateway.AsyncMotionMulticast.Start_listen",
        side_effect=socket.gaierror,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: TEST_API_KEY}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_GATEWAY_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_API_KEY: TEST_API_KEY,
            const.CONF_INTERFACE: TEST_HOST_ANY,
        }
    )


@test
async def dhcp_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Successful flow from DHCP discovery."""
    dhcp_data = DhcpServiceInfo(
        ip=TEST_HOST,
        hostname="MOTION_abcdef",
        macaddress=DHCP_FORMATTED_MAC,
    )

    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=dhcp_data
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("connect")
    expect(result["errors"]).to_equal({})

    with patch(
        "homeassistant.components.motion_blinds.gateway.AsyncMotionMulticast.Start_listen",
        side_effect=OSError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_API_KEY: TEST_API_KEY}
        )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(DEFAULT_GATEWAY_NAME)
    expect(result["data"]).to_equal(
        {
            CONF_HOST: TEST_HOST,
            CONF_API_KEY: TEST_API_KEY,
            const.CONF_INTERFACE: TEST_HOST_ANY,
        }
    )


@test
async def dhcp_flow_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that DHCP discovery aborts if not Motionblinds."""
    dhcp_data = DhcpServiceInfo(
        ip=TEST_HOST,
        hostname="MOTION_abcdef",
        macaddress=DHCP_FORMATTED_MAC,
    )

    with patch(
        "homeassistant.components.motion_blinds.config_flow.MotionGateway.GetDeviceList",
        side_effect=socket.timeout,
    ):
        result = await hass.config_entries.flow.async_init(
            const.DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=dhcp_data
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_motionblinds")


@test
async def dhcp_flow_abort_invalid_response(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that DHCP discovery aborts if device responded with invalid data."""
    dhcp_data = DhcpServiceInfo(
        ip=TEST_HOST,
        hostname="MOTION_abcdef",
        macaddress=DHCP_FORMATTED_MAC,
    )

    with patch(
        "homeassistant.components.motion_blinds.config_flow.MotionGateway.available",
        False,
    ):
        result = await hass.config_entries.flow.async_init(
            const.DOMAIN, context={"source": config_entries.SOURCE_DHCP}, data=dhcp_data
        )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("not_motionblinds")


@test
async def options_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test specifying non default settings using options flow."""
    config_entry = MockConfigEntry(
        domain=const.DOMAIN,
        unique_id=TEST_MAC,
        data={CONF_HOST: TEST_HOST, CONF_API_KEY: TEST_API_KEY},
        title=DEFAULT_GATEWAY_NAME,
    )
    config_entry.add_to_hass(hass)

    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("init")

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={const.CONF_WAIT_FOR_PUSH: False},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(config_entry.options).to_equal({const.CONF_WAIT_FOR_PUSH: False})


@test
async def change_connection_settings(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test changing connection settings by issuing a second user config flow."""
    config_entry = MockConfigEntry(
        domain=const.DOMAIN,
        unique_id=TEST_MAC,
        data={
            CONF_HOST: TEST_HOST,
            CONF_API_KEY: TEST_API_KEY,
            const.CONF_INTERFACE: TEST_HOST_HA,
        },
        title=DEFAULT_GATEWAY_NAME,
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        const.DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: TEST_HOST2}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("connect")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_API_KEY: TEST_API_KEY2}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(config_entry.data[CONF_HOST]).to_equal(TEST_HOST2)
    expect(config_entry.data[CONF_API_KEY]).to_equal(TEST_API_KEY2)
    expect(config_entry.data[const.CONF_INTERFACE]).to_equal(TEST_HOST_ANY)
