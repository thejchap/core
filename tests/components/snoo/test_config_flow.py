"""Test the Happiest Baby Snoo config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from python_snoo.exceptions import InvalidSnooAuth, SnooAuthException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.snoo.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import create_entry
from ._fixtures import bypass_api, mock_setup_entry

from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def config_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    api: AsyncMock = Depends(bypass_api),
) -> None:
    """Test we create the entry successfully."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test-username")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        }
    )
    expect(result["result"].unique_id).to_equal("123e4567-e89b-12d3-a456-426614174000")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case(
        "invalid_auth", exception=InvalidSnooAuth, error_msg="invalid_auth"
    ),
    test.case(
        "cannot_connect", exception=SnooAuthException, error_msg="cannot_connect"
    ),
    test.case("unknown", exception=Exception, error_msg="unknown"),
)
async def form_auth_issues(
    exception: type[Exception],
    error_msg: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    api: AsyncMock = Depends(bypass_api),
) -> None:
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    api.authorize.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error_msg})
    api.authorize.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test-username")
    expect(result["data"]).to_equal(
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        }
    )
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def account_already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
    _api: AsyncMock = Depends(bypass_api),
) -> None:
    """Ensure we abort if the config flow already exists."""
    create_entry(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_USERNAME: "test-username",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
