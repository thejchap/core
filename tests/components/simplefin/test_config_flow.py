"""Test config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from simplefin4py.exceptions import (
    SimpleFinAuthError,
    SimpleFinClaimError,
    SimpleFinInvalidAccountURLError,
    SimpleFinInvalidClaimTokenError,
    SimpleFinPaymentRequiredError,
)
from tryke import Depends, expect, fixture, test

from homeassistant.components.simplefin import CONF_ACCESS_URL
from homeassistant.components.simplefin.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import (
    MOCK_ACCESS_URL,
    mock_config_entry,
    mock_setup_entry,
    mock_simplefin_client,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def successful_claim(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    client: AsyncMock = Depends(mock_simplefin_client),
) -> None:
    """Test successful token claim in config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_URL: "donJulio"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("SimpleFIN")
    expect(result["data"]).to_equal({CONF_ACCESS_URL: MOCK_ACCESS_URL})


@test
async def already_setup(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    client: AsyncMock = Depends(mock_simplefin_client),
) -> None:
    """Test already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_URL: MOCK_ACCESS_URL},
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def access_url(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_simplefin_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test standard config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_URL: "http://user:password@string"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"][CONF_ACCESS_URL]).to_equal("http://user:password@string")
    expect(result["title"]).to_equal("SimpleFIN")


@test.cases(
    test.case(
        "url_error",
        side_effect=SimpleFinInvalidAccountURLError,
        error_key="url_error",
    ),
    test.case(
        "payment_required",
        side_effect=SimpleFinPaymentRequiredError,
        error_key="payment_required",
    ),
    test.case(
        "auth_error",
        side_effect=SimpleFinAuthError,
        error_key="invalid_auth",
    ),
)
async def access_url_errors(
    side_effect: type[Exception],
    error_key: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_simplefin_client),
) -> None:
    """Test the various errors we can get in access_url mode."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    client.claim_setup_token.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_URL: "donJulio"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_key})

    client.claim_setup_token.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_URL: "http://user:password@string"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_ACCESS_URL: "http://user:password@string"})
    expect(result["title"]).to_equal("SimpleFIN")


@test.cases(
    test.case(
        "invalid_claim_token",
        side_effect=SimpleFinInvalidClaimTokenError,
        error_key="invalid_claim_token",
    ),
    test.case(
        "claim_error",
        side_effect=SimpleFinClaimError,
        error_key="claim_error",
    ),
)
async def claim_token_errors(
    side_effect: type[Exception],
    error_key: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: AsyncMock = Depends(mock_simplefin_client),
) -> None:
    """Test config flow with various token claim errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)

    client.claim_setup_token.side_effect = side_effect

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_URL: "donJulio"},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_key})

    client.claim_setup_token.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_ACCESS_URL: "donJulio"},
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal({CONF_ACCESS_URL: "https://i:am@yomama.house.com"})
    expect(result["title"]).to_equal("SimpleFIN")
