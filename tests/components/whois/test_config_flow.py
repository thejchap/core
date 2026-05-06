"""Tests for the Whois config flow."""

from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test
from whois.exceptions import (
    FailedParsingWhoisOutput,
    UnknownDateFormat,
    UnknownTld,
    WhoisCommandFailed,
    WhoisPrivateRegistry,
    WhoisQuotaExceeded,
)

from homeassistant.components.whois.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_config_entry, mock_setup_entry, mock_whois

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_user_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _whois: MagicMock = Depends(mock_whois),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test the full user configuration flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_DOMAIN: "Example.com"},
    )

    expect(result2.get("type")).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2.get("title")).to_equal("Example.com")
    expect(result2.get("data")).to_equal({CONF_DOMAIN: "example.com"})

    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("unknown_tld", throw=UnknownTld, reason="unknown_tld"),
    test.case(
        "unexpected_response",
        throw=FailedParsingWhoisOutput,
        reason="unexpected_response",
    ),
    test.case(
        "unknown_date_format",
        throw=UnknownDateFormat,
        reason="unknown_date_format",
    ),
    test.case(
        "whois_command_failed",
        throw=WhoisCommandFailed,
        reason="whois_command_failed",
    ),
    test.case(
        "private_registry", throw=WhoisPrivateRegistry, reason="private_registry"
    ),
    test.case("quota_exceeded", throw=WhoisQuotaExceeded, reason="quota_exceeded"),
)
async def full_flow_with_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    whois: MagicMock = Depends(mock_whois),
    *,
    throw: type[Exception],
    reason: str,
) -> None:
    """Test the full user configuration flow with an error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result.get("type")).to_be(FlowResultType.FORM)
    expect(result.get("step_id")).to_equal("user")

    whois.side_effect = throw
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_DOMAIN: "Example.com"},
    )

    expect(result2.get("type")).to_be(FlowResultType.FORM)
    expect(result2.get("step_id")).to_equal("user")
    expect(result2.get("errors")).to_equal({"base": reason})

    expect(len(setup_entry.mock_calls)).to_equal(0)
    expect(len(whois.mock_calls)).to_equal(1)

    whois.side_effect = None
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={CONF_DOMAIN: "Example.com"},
    )

    expect(result3.get("type")).to_be(FlowResultType.CREATE_ENTRY)

    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(whois.mock_calls)).to_equal(2)


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _whois: MagicMock = Depends(mock_whois),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test we abort if already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
        data={CONF_DOMAIN: "HOME-Assistant.io"},
    )

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")

    expect(len(setup_entry.mock_calls)).to_equal(0)
