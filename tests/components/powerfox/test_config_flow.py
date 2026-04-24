"""Test the Powerfox config flow."""

from __future__ import annotations

from ipaddress import ip_address
from unittest.mock import AsyncMock, MagicMock, patch

from powerfox import PowerfoxAuthenticationError, PowerfoxConnectionError
from tryke import Depends, expect, fixture, test

from homeassistant.components.powerfox.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.zeroconf import ZeroconfServiceInfo

from . import MOCK_DIRECT_HOST

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

from ._fixtures import (
    mock_async_zeroconf as mock_async_zeroconf_fx,
    mock_config_entry as mock_config_entry_fx,
    mock_powerfox_client as mock_powerfox_client_fx,
    mock_setup_entry as mock_setup_entry_fx,
)

MOCK_ZEROCONF_DISCOVERY_INFO = ZeroconfServiceInfo(
    ip_address=ip_address(MOCK_DIRECT_HOST),
    ip_addresses=[ip_address(MOCK_DIRECT_HOST)],
    hostname="powerfox.local",
    name="Powerfox",
    port=443,
    type="_http._tcp",
    properties={},
)


@fixture
def _trigger_executor(
    _net: None = Depends(mock_network),
    _zc: MagicMock = Depends(mock_async_zeroconf_fx),
    _setup: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Wire network + zeroconf + setup for every test."""


@test
async def full_user_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_powerfox_client: AsyncMock = Depends(mock_powerfox_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(bool(result.get("errors"))).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@powerfox.test", CONF_PASSWORD: "test-password"},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("test@powerfox.test")
    expect(result.get("data")).to_equal(
        {CONF_EMAIL: "test@powerfox.test", CONF_PASSWORD: "test-password"}
    )
    expect(len(mock_powerfox_client.all_devices.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def zeroconf_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_powerfox_client: AsyncMock = Depends(mock_powerfox_client_fx),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test zeroconf discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DISCOVERY_INFO,
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")
    expect(bool(result.get("errors"))).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@powerfox.test", CONF_PASSWORD: "test-password"},
    )

    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result.get("title")).to_equal("test@powerfox.test")
    expect(result.get("data")).to_equal(
        {CONF_EMAIL: "test@powerfox.test", CONF_PASSWORD: "test-password"}
    )
    expect(len(mock_powerfox_client.all_devices.mock_calls)).to_equal(1)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def duplicate_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_powerfox_client: AsyncMock = Depends(mock_powerfox_client_fx),
) -> None:
    """Test abort when setting up duplicate entry."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(bool(result.get("errors"))).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@powerfox.test", CONF_PASSWORD: "test-password"},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test
async def duplicate_entry_reconfiguration(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_powerfox_client: AsyncMock = Depends(mock_powerfox_client_fx),
) -> None:
    """Test abort when setting up duplicate entry on reconfiguration."""
    mock_config_entry.add_to_hass(hass)
    mock_config_entry_2 = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_EMAIL: "new@powerfox.test", CONF_PASSWORD: "new-password"},
    )
    mock_config_entry_2.add_to_hass(hass)
    expect(len(hass.config_entries.async_entries())).to_equal(2)

    result = await mock_config_entry_2.start_reconfigure_flow(hass)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@powerfox.test", CONF_PASSWORD: "test-password"},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")


@test.cases(
    test.case("connection", PowerfoxConnectionError, "cannot_connect"),
    test.case("auth", PowerfoxAuthenticationError, "invalid_auth"),
)
async def exceptions(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_powerfox_client: AsyncMock = Depends(mock_powerfox_client_fx),
) -> None:
    """Test exceptions during config flow."""
    mock_powerfox_client.all_devices.side_effect = exception
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@powerfox.test", CONF_PASSWORD: "test-password"},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": error})

    mock_powerfox_client.all_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_EMAIL: "test@powerfox.test", CONF_PASSWORD: "test-password"},
    )
    expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)


@test
async def step_reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test re-authentication flow."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    with patch(
        "homeassistant.components.powerfox.config_flow.Powerfox",
        autospec=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={CONF_PASSWORD: "new-password"},
        )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")
    expect(len(hass.config_entries.async_entries())).to_equal(1)
    expect(mock_config_entry.data[CONF_PASSWORD]).to_equal("new-password")


@test.cases(
    test.case("connection", PowerfoxConnectionError, "cannot_connect"),
    test.case("auth", PowerfoxAuthenticationError, "invalid_auth"),
)
async def step_reauth_exceptions(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_powerfox_client: AsyncMock = Depends(mock_powerfox_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test exceptions during re-authentication flow."""
    mock_powerfox_client.all_devices.side_effect = exception
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reauth_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "new-password"},
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": error})

    mock_powerfox_client.all_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "new-password"},
    )
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")
    expect(len(hass.config_entries.async_entries())).to_equal(1)
    expect(mock_config_entry.data[CONF_PASSWORD]).to_equal("new-password")


@test
async def reconfigure(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
    mock_powerfox_client: AsyncMock = Depends(mock_powerfox_client_fx),
) -> None:
    """Test reconfiguration of existing entry."""
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_EMAIL: "new-email@powerfox.test",
            CONF_PASSWORD: "new-password",
        },
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")
    expect(len(hass.config_entries.async_entries())).to_equal(1)
    expect(mock_config_entry.data[CONF_EMAIL]).to_equal("new-email@powerfox.test")
    expect(mock_config_entry.data[CONF_PASSWORD]).to_equal("new-password")


@test.cases(
    test.case("connection", PowerfoxConnectionError, "cannot_connect"),
    test.case("auth", PowerfoxAuthenticationError, "invalid_auth"),
)
async def reconfigure_exceptions(
    exception: Exception,
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_powerfox_client: AsyncMock = Depends(mock_powerfox_client_fx),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry_fx),
) -> None:
    """Test exceptions during reconfiguration flow."""
    mock_powerfox_client.all_devices.side_effect = exception
    mock_config_entry.add_to_hass(hass)
    result = await mock_config_entry.start_reconfigure_flow(hass)

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_EMAIL: "new-email@powerfox.test",
            CONF_PASSWORD: "new-password",
        },
    )
    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("errors")).to_equal({"base": error})

    mock_powerfox_client.all_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_EMAIL: "new-email@powerfox.test",
            CONF_PASSWORD: "new-password",
        },
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")
    expect(len(hass.config_entries.async_entries())).to_equal(1)
    expect(mock_config_entry.data[CONF_EMAIL]).to_equal("new-email@powerfox.test")
    expect(mock_config_entry.data[CONF_PASSWORD]).to_equal("new-password")
