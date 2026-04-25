"""Define tests for the Elexa Guardian config flow."""

from ipaddress import ip_address
from typing import Any
from unittest.mock import patch

from aioguardian.errors import GuardianError
from tryke import Depends, expect, fixture, test

from homeassistant.components.guardian import CONF_UID, DOMAIN
from homeassistant.components.guardian.config_flow import (
    async_get_pin_from_discovery_hostname,
    async_get_pin_from_uid,
)
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_IP_ADDRESS, CONF_PORT
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import (
    config as config_fx,
    config_entry as config_entry_fx,
    mock_setup_entry,
    setup_guardian as setup_guardian_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _setup: object = Depends(mock_setup_entry),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def duplicate_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config_fx),
    _config_entry: MockConfigEntry = Depends(config_entry_fx),
    _setup_guardian: None = Depends(setup_guardian_fx),
) -> None:
    """Test that errors are shown when duplicate entries are added."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=config
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def connect_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config_fx),
) -> None:
    """Test that the config entry errors out if the device cannot connect."""
    with patch(
        "aioguardian.client.Client.connect",
        side_effect=GuardianError,
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}, data=config
        )
        expect(result["type"]).to_be(FlowResultType.FORM)
        expect(result["errors"]).to_equal({CONF_IP_ADDRESS: "cannot_connect"})


@test
async def get_pin_from_discovery_hostname(
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test getting a device PIN from the zeroconf-discovered hostname."""
    pin = async_get_pin_from_discovery_hostname("GVC1-3456.local.")
    expect(pin).to_equal("3456")


@test
async def get_pin_from_uid(
    _trigger: None = Depends(_trigger_executor),
) -> None:
    """Test getting a device PIN from its UID."""
    pin = async_get_pin_from_uid("ABCDEF123456")
    expect(pin).to_equal("3456")


@test
async def step_user(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config: dict[str, Any] = Depends(config_fx),
    _setup_guardian: None = Depends(setup_guardian_fx),
) -> None:
    """Test the user step."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}, data=config
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("ABCDEF123456")
    expect(result["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_PORT: 7777,
            CONF_UID: "ABCDEF123456",
        }
    )


@test
async def step_zeroconf(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_guardian: None = Depends(setup_guardian_fx),
) -> None:
    """Test the zeroconf step."""
    zeroconf_data = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.100"),
        ip_addresses=[ip_address("192.168.1.100")],
        port=7777,
        hostname="GVC1-ABCD.local.",
        type="_api._udp.local.",
        name="Guardian Valve Controller API._api._udp.local.",
        properties={"_raw": {}},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=zeroconf_data
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("ABCDEF123456")
    expect(result["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_PORT: 7777,
            CONF_UID: "ABCDEF123456",
        }
    )


@test
async def step_zeroconf_already_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the zeroconf step aborting because it's already in progress."""
    zeroconf_data = ZeroconfServiceInfo(
        ip_address=ip_address("192.168.1.100"),
        ip_addresses=[ip_address("192.168.1.100")],
        port=7777,
        hostname="GVC1-ABCD.local.",
        type="_api._udp.local.",
        name="Guardian Valve Controller API._api._udp.local.",
        properties={"_raw": {}},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=zeroconf_data
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=zeroconf_data
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test
async def step_dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_guardian: None = Depends(setup_guardian_fx),
) -> None:
    """Test the dhcp step."""
    dhcp_data = DhcpServiceInfo(
        ip="192.168.1.100",
        hostname="GVC1-ABCD.local.",
        macaddress="aabbccddeeff",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=dhcp_data
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("ABCDEF123456")
    expect(result["data"]).to_equal(
        {
            CONF_IP_ADDRESS: "192.168.1.100",
            CONF_PORT: 7777,
            CONF_UID: "ABCDEF123456",
        }
    )


@test
async def step_dhcp_already_in_progress(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test the zeroconf step aborting because it's already in progress."""
    dhcp_data = DhcpServiceInfo(
        ip="192.168.1.100",
        hostname="GVC1-ABCD.local.",
        macaddress="aabbccddeeff",
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=dhcp_data
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=dhcp_data
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_in_progress")


@test
async def step_dhcp_already_setup_match_mac(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if the device is already setup with matching unique id and discovered via DHCP."""
    entry = MockConfigEntry(
        domain=DOMAIN, data={CONF_IP_ADDRESS: "1.2.3.4"}, unique_id="guardian_ABCD"
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.100",
            hostname="GVC1-ABCD.local.",
            macaddress="aabbccddabcd",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def step_dhcp_already_setup_match_ip(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test we abort if the device is already setup with matching ip and discovered via DHCP."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_IP_ADDRESS: "192.168.1.100"},
        unique_id="guardian_0000",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.1.100",
            hostname="GVC1-ABCD.local.",
            macaddress="aabbccddabcd",
        ),
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
