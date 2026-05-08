"""Tests for the BSBLan device config flow."""

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock

from bsblan import BSBLANAuthError, BSBLANConnectionError, BSBLANError
from tryke import Depends, expect, fixture, test

from homeassistant.components.bsblan.const import (
    CONF_HEATING_CIRCUITS,
    CONF_PASSKEY,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.device_registry import format_mac
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from ._fixtures import mock_bsblan, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


ZEROCONF_DISCOVERY_INFO = ZeroconfServiceInfo(
    ip_address=ip_address("10.0.2.60"),
    ip_addresses=[ip_address("10.0.2.60")],
    name="BSB-LAN web service._http._tcp.local.",
    type="_http._tcp.local.",
    properties={"mac": "00:80:41:19:69:90"},
    port=80,
    hostname="BSB-LAN.local.",
)


@fixture
def _trigger_executor(
    hass: HomeAssistant = Depends(hass_fixture),
    _network: None = Depends(mock_network),
) -> HomeAssistant:
    """Anchor fixture so tryke fully resolves hass."""
    return hass


@test
async def full_user_flow_implementation(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    bsblan_mock: MagicMock = Depends(mock_bsblan),
    setup_mock: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 80,
            CONF_PASSKEY: "1234",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "admin1234",
        },
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("BSB-LAN")
    expect(result.get("data")).to_equal(
        {
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 80,
            CONF_PASSKEY: "1234",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "admin1234",
            CONF_HEATING_CIRCUITS: [1],
        }
    )
    expect(result["result"].unique_id).to_equal(format_mac("00:80:41:19:69:90"))

    expect(len(setup_mock.mock_calls)).to_equal(1)
    expect(len(bsblan_mock.device.mock_calls)).to_equal(1)


@test
async def show_user_form(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Test that the user set up form is served."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")


@test.cases(
    test.case("bsblan_error", side_effect=BSBLANError),
    test.case("timeout", side_effect=TimeoutError),
)
async def circuit_discovery_failure_falls_back_to_default(
    *,
    side_effect: type[Exception],
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    bsblan_mock: MagicMock = Depends(mock_bsblan),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test that circuit discovery failure falls back to single circuit."""
    bsblan_mock.initialize.side_effect = side_effect

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 80,
            CONF_PASSKEY: "1234",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "admin1234",
        },
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("data")[CONF_HEATING_CIRCUITS]).to_equal([1])


@test
async def connection_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    bsblan_mock: MagicMock = Depends(mock_bsblan),
) -> None:
    """Test we show user form on BSBLan connection error."""
    bsblan_mock.device.side_effect = BSBLANConnectionError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 80,
            CONF_PASSKEY: "1234",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "admin1234",
        },
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(result.get("errors")).to_equal({"base": "cannot_connect"})


@test
async def authentication_error(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    bsblan_mock: MagicMock = Depends(mock_bsblan),
) -> None:
    """Test we show user form on BSBLan auth error."""
    bsblan_mock.device.side_effect = BSBLANAuthError

    user_input = {
        CONF_HOST: "192.168.1.100",
        CONF_PORT: 8080,
        CONF_PASSKEY: "secret",
        CONF_USERNAME: "testuser",
        CONF_PASSWORD: "wrongpassword",
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data=user_input,
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": "invalid_auth"})
    expect(result.get("step_id")).to_equal("user")


@test
async def user_device_exists_abort(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _bsblan: MagicMock = Depends(mock_bsblan),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test that we abort if entry already exists."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 80,
            CONF_PASSKEY: "1234",
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "admin1234",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def abort_if_existing_entry_for_zeroconf(
    _trigger: HomeAssistant = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _bsblan: MagicMock = Depends(mock_bsblan),
) -> None:
    """Test we abort if same host/port already exists during zeroconf discovery."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_HOST: "127.0.0.1",
            CONF_PORT: 80,
            CONF_USERNAME: "admin",
            CONF_PASSWORD: "admin1234",
        },
        unique_id="00:80:41:19:69:90",
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZEROCONF_DISCOVERY_INFO,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.skip("zeroconf flow tests need additional fixtures and discovery info")
async def zeroconf_discovery(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test zeroconf discovery flow."""


@test.skip("reauth flow tests not yet ported")
async def reauth_flow_success(
    _trigger: HomeAssistant = Depends(_trigger_executor),
) -> None:
    """Test reauth flow success."""
