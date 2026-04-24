"""Test the Rehlko config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from aiokem import AuthenticationCredentialsError
from tryke import Depends, expect, fixture, test

from homeassistant.components.rehlko import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from ._fixtures import (
    TEST_EMAIL,
    TEST_PASSWORD,
    TEST_SUBJECT,
    mock_rehlko as mock_rehlko_fx,
    mock_setup_entry as mock_setup_entry_fx,
    rehlko_config_entry as rehlko_config_entry_fx,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network

DHCP_DISCOVERY = DhcpServiceInfo(
    ip="1.1.1.1",
    hostname="KohlerGen",
    macaddress="00146faabbcc",
)


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def configure_entry(
    hass: HomeAssistant = Depends(hass_fixture),
    _rehlko: AsyncMock = Depends(mock_rehlko_fx),
    setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we can configure the entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_EMAIL.lower())
    expect(result["data"]).to_equal(
        {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}
    )
    expect(result["result"].unique_id).to_equal(TEST_SUBJECT)
    expect(setup_entry.call_count).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth",
        error=AuthenticationCredentialsError,
        conf_error={CONF_PASSWORD: "invalid_auth"},
    ),
    test.case("timeout", error=TimeoutError, conf_error={"base": "cannot_connect"}),
    test.case("unknown", error=Exception, conf_error={"base": "unknown"}),
)
async def configure_entry_exceptions(
    *,
    error: type[Exception],
    conf_error: dict[str, str],
    hass: HomeAssistant = Depends(hass_fixture),
    rehlko: AsyncMock = Depends(mock_rehlko_fx),
    setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we handle a variety of exceptions and recover by adding new entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    rehlko.authenticate.side_effect = error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal(conf_error)
    expect(setup_entry.call_count).to_equal(0)

    rehlko.authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(TEST_EMAIL.lower())
    expect(result["data"]).to_equal(
        {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}
    )
    expect(result["result"].unique_id).to_equal(TEST_SUBJECT)
    expect(setup_entry.call_count).to_equal(1)


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(rehlko_config_entry_fx),
    _rehlko: AsyncMock = Depends(mock_rehlko_fx),
) -> None:
    """Test if entry is already configured."""
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(rehlko_config_entry_fx),
    _rehlko: AsyncMock = Depends(mock_rehlko_fx),
    setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test reauth flow."""
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: TEST_PASSWORD + "new"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(entry.data[CONF_PASSWORD]).to_equal(TEST_PASSWORD + "new")
    expect(setup_entry.call_count).to_equal(1)


@test
async def reauth_exception(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(rehlko_config_entry_fx),
    rehlko: AsyncMock = Depends(mock_rehlko_fx),
    _setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test reauth flow recovers from an auth error."""
    entry.add_to_hass(hass)
    result = await entry.start_reauth_flow(hass)

    rehlko.authenticate.side_effect = AuthenticationCredentialsError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: TEST_PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"password": "invalid_auth"})

    rehlko.authenticate.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: TEST_PASSWORD + "new"}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def dhcp_discovery(
    hass: HomeAssistant = Depends(hass_fixture),
    _rehlko: AsyncMock = Depends(mock_rehlko_fx),
    _setup_entry: AsyncMock = Depends(mock_setup_entry_fx),
) -> None:
    """Test we can setup from dhcp discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_DISCOVERY
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_EMAIL: TEST_EMAIL, CONF_PASSWORD: TEST_PASSWORD}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def dhcp_discovery_already_set_up(
    hass: HomeAssistant = Depends(hass_fixture),
    entry: MockConfigEntry = Depends(rehlko_config_entry_fx),
    _rehlko: AsyncMock = Depends(mock_rehlko_fx),
) -> None:
    """Test DHCP discovery aborts if already set up."""
    entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_DISCOVERY
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
