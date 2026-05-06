"""Tests for the TOLO Sauna config flow."""

from unittest.mock import Mock

from tololib import ToloCommunicationError
from tryke import Depends, expect, fixture, test

from homeassistant.components.tolo.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import (
    config_entry as config_entry_fixture,
    coordinator_toloclient,
    toloclient,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

MOCK_DHCP_DATA = DhcpServiceInfo(
    ip="127.0.0.2", macaddress="001122334455", hostname="mock_hostname"
)


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_with_timed_out_host(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(toloclient),
) -> None:
    """Test a user initiated config flow with provided host which times out."""
    client().get_status.side_effect = ToloCommunicationError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_HOST: "127.0.0.1"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})


@test
async def user_walkthrough(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(toloclient),
    _coord: Mock = Depends(coordinator_toloclient),
) -> None:
    """Test complete user flow with first wrong and then correct host."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    client().get_status.side_effect = lambda *args, **kwargs: None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.2"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    client().get_status.side_effect = lambda *args, **kwargs: object()

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "127.0.0.1"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("TOLO Sauna")
    expect(result["data"][CONF_HOST]).to_equal("127.0.0.1")


@test
async def dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(toloclient),
    _coord: Mock = Depends(coordinator_toloclient),
) -> None:
    """Test starting a flow from discovery."""
    client().get_status.side_effect = lambda *args, **kwargs: object()

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=MOCK_DHCP_DATA
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("TOLO Sauna")
    expect(result["data"][CONF_HOST]).to_equal("127.0.0.2")
    expect(result["result"].unique_id).to_equal("00:11:22:33:44:55")


@test
async def dhcp_invalid_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(toloclient),
) -> None:
    """Test starting a flow from discovery."""
    client().get_status.side_effect = lambda *args, **kwargs: None

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=MOCK_DHCP_DATA
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)


@test
async def reconfigure_walkthrough(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(toloclient),
    _coord: Mock = Depends(coordinator_toloclient),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test a reconfigure flow without problems."""
    config_entry.add_to_hass(hass)
    client().get_status.side_effect = lambda *args, **kwargs: object()
    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "127.0.0.4"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_HOST]).to_equal("127.0.0.4")


@test
async def reconfigure_error_then_fix(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(toloclient),
    _coord: Mock = Depends(coordinator_toloclient),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test a reconfigure flow which first fails and then recovers."""
    config_entry.add_to_hass(hass)
    client().get_status.side_effect = lambda *args, **kwargs: object()
    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["step_id"]).to_equal("user")

    client().get_status.side_effect = ToloCommunicationError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "127.0.0.5"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]["base"]).to_equal("cannot_connect")

    client().get_status.side_effect = None
    client().get_status.side_effect = lambda *args, **kwargs: object()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "127.0.0.4"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    expect(config_entry.data[CONF_HOST]).to_equal("127.0.0.4")


@test
async def reconfigure_duplicate_ip(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: Mock = Depends(toloclient),
    _coord: Mock = Depends(coordinator_toloclient),
    config_entry: MockConfigEntry = Depends(config_entry_fixture),
) -> None:
    """Test a reconfigure flow where the user is trying to have to entries with the same IP."""
    config_entry.add_to_hass(hass)
    client().get_status.side_effect = lambda *args, **kwargs: object()
    config_entry2 = MockConfigEntry(
        domain=DOMAIN, data={CONF_HOST: "127.0.0.6"}, unique_id="second_entry"
    )
    config_entry2.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "127.0.0.6"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(config_entry.data[CONF_HOST]).to_equal("127.0.0.1")
