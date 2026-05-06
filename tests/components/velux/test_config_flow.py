"""Test the Velux config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pyvlx import PyVLXException
from tryke import Depends, expect, fixture, test

from homeassistant.components.velux import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER, ConfigEntryState
from homeassistant.const import CONF_HOST, CONF_MAC, CONF_NAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import (
    mock_config_entry,
    mock_discovered_config_entry,
    mock_pyvlx,
    mock_setup_entry,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


DHCP_DISCOVERY = DhcpServiceInfo(
    ip="127.0.0.1",
    hostname="VELUX_KLF_LAN_ABCD",
    macaddress="64618400abcd",
)


@test
async def user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    pyvlx: AsyncMock = Depends(mock_pyvlx),
) -> None:
    """Test starting a flow by user with valid values."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "NotAStrongPassword",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("127.0.0.1")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "NotAStrongPassword",
        }
    )
    expect(bool(result["result"].unique_id)).to_be(False)

    pyvlx.disconnect.assert_called_once()
    pyvlx.connect.assert_called_once()


@test.cases(
    test.case(
        "invalid_auth",
        exception=PyVLXException("Login to KLF 200 failed, check credentials"),
        error="invalid_auth",
    ),
    test.case(
        "cannot_connect", exception=PyVLXException("DUMMY"), error="cannot_connect"
    ),
    test.case("unknown", exception=Exception("DUMMY"), error="unknown"),
)
async def user_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pyvlx: AsyncMock = Depends(mock_pyvlx),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test starting a flow by user but with exceptions."""
    pyvlx.connect.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "NotAStrongPassword",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": error})

    pyvlx.connect.assert_called_once()

    pyvlx.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "NotAStrongPassword",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def user_flow_duplicate_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test initialized flow with a duplicate entry."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_HOST: "127.0.0.1",
            CONF_PASSWORD: "NotAStrongPassword",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    pyvlx: AsyncMock = Depends(mock_pyvlx),
) -> None:
    """Test that reauth flow works with valid credentials."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: "New Password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(config_entry.data[CONF_PASSWORD]).to_equal("New Password")

    pyvlx.connect.assert_called_once()
    pyvlx.disconnect.assert_called_once()


@test.cases(
    test.case(
        "invalid_auth",
        exception=PyVLXException("Login to KLF 200 failed, check credentials"),
        error="invalid_auth",
    ),
    test.case(
        "cannot_connect", exception=PyVLXException("DUMMY"), error="cannot_connect"
    ),
    test.case("unknown", exception=Exception("DUMMY"), error="unknown"),
)
async def reauth_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pyvlx: AsyncMock = Depends(mock_pyvlx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test error handling in reauth flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    pyvlx.connect.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: "New Password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": error})

    pyvlx.connect.assert_called_once()
    pyvlx.disconnect.assert_not_called()

    pyvlx.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "New Password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(config_entry.data[CONF_PASSWORD]).to_equal("New Password")

    pyvlx.disconnect.assert_called_once()


@test
async def dhcp_discovery(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pyvlx: AsyncMock = Depends(mock_pyvlx),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we can setup from dhcp discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_DISCOVERY,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "NotAStrongPassword"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("VELUX_KLF_ABCD")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "127.0.0.1",
            CONF_MAC: "64:61:84:00:ab:cd",
            CONF_NAME: "VELUX_KLF_ABCD",
            CONF_PASSWORD: "NotAStrongPassword",
        }
    )
    expect(result["result"].unique_id).to_equal("VELUX_KLF_ABCD")

    pyvlx.disconnect.assert_called()
    pyvlx.connect.assert_called()


@test.cases(
    test.case(
        "invalid_auth",
        exception=PyVLXException("Login to KLF 200 failed, check credentials"),
        error="invalid_auth",
    ),
    test.case(
        "cannot_connect", exception=PyVLXException("DUMMY"), error="cannot_connect"
    ),
    test.case("unknown", exception=Exception("DUMMY"), error="unknown"),
)
async def dhcp_discovery_errors(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    pyvlx: AsyncMock = Depends(mock_pyvlx),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test we can setup from dhcp discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_DISCOVERY,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")

    pyvlx.connect.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "NotAStrongPassword"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("discovery_confirm")
    expect(result["errors"]).to_equal({"base": error})

    pyvlx.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "NotAStrongPassword"},
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("VELUX_KLF_ABCD")
    expect(result["data"]).to_equal(
        {
            CONF_HOST: "127.0.0.1",
            CONF_MAC: "64:61:84:00:ab:cd",
            CONF_NAME: "VELUX_KLF_ABCD",
            CONF_PASSWORD: "NotAStrongPassword",
        }
    )


@test
async def dhcp_discovery_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pyvlx: AsyncMock = Depends(mock_pyvlx),
    config_entry: MockConfigEntry = Depends(mock_discovered_config_entry),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test dhcp discovery when already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def dhcp_discover_unique_id(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup: AsyncMock = Depends(mock_setup_entry),
    _pyvlx: AsyncMock = Depends(mock_pyvlx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test dhcp discovery with unique id."""
    config_entry.add_to_hass(hass)
    expect(await hass.config_entries.async_setup(config_entry.entry_id)).to_be(True)

    expect(config_entry.state).to_be(ConfigEntryState.LOADED)
    expect(config_entry.unique_id).to_be(None)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(config_entry.unique_id).to_equal("VELUX_KLF_ABCD")


@test
async def dhcp_discovery_not_loaded(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _pyvlx: AsyncMock = Depends(mock_pyvlx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test dhcp discovery when entry with same host not loaded."""
    config_entry.add_to_hass(hass)

    expect(config_entry.state is ConfigEntryState.LOADED).to_be(False)
    expect(config_entry.unique_id).to_be(None)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_DISCOVERY,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")

    expect(config_entry.unique_id).to_be(None)
