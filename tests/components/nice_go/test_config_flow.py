"""Test the Nice G.O. config flow."""

from unittest.mock import AsyncMock

from nice_go import AuthFailedError
from tryke import Depends, expect, fixture, test

from homeassistant.components.nice_go.const import (
    CONF_REFRESH_TOKEN,
    CONF_REFRESH_TOKEN_CREATION_TIME,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import setup_integration
from ._fixtures import mock_config_entry, mock_nice_go, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import freezer, hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Anchor fixture."""


@test
async def form(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    nice_go: AsyncMock = Depends(mock_nice_go),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _freezer=Depends(freezer),
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(not result["errors"]).to_be(True)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-email",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test-email")
    expect(result["data"][CONF_EMAIL]).to_equal("test-email")
    expect(result["data"][CONF_PASSWORD]).to_equal("test-password")
    expect(result["data"][CONF_REFRESH_TOKEN]).to_equal("test-refresh-token")
    expect(CONF_REFRESH_TOKEN_CREATION_TIME in result["data"]).to_be(True)
    expect(result["result"].unique_id).to_equal("test-email")
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("auth_failed", side_effect=AuthFailedError, expected_error="invalid_auth"),
    test.case("unknown", side_effect=Exception, expected_error="unknown"),
)
async def form_exceptions(
    side_effect: type[Exception],
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    nice_go: AsyncMock = Depends(mock_nice_go),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test we handle invalid auth."""
    nice_go.authenticate.side_effect = side_effect
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-email",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})
    nice_go.authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-email",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def duplicate_device(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    nice_go: AsyncMock = Depends(mock_nice_go),
) -> None:
    """Test that duplicate devices are handled."""
    config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-email",
            CONF_PASSWORD: "test-password",
        },
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    nice_go: AsyncMock = Depends(mock_nice_go),
) -> None:
    """Test reauth flow."""
    await setup_integration(hass, config_entry, [])

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-email",
            CONF_PASSWORD: "other-fake-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case("auth_failed", side_effect=AuthFailedError, expected_error="invalid_auth"),
    test.case("unknown", side_effect=Exception, expected_error="unknown"),
)
async def reauth_exceptions(
    side_effect: type[Exception],
    expected_error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    nice_go: AsyncMock = Depends(mock_nice_go),
) -> None:
    """Test we handle invalid auth on reauth."""
    nice_go.authenticate.side_effect = side_effect
    await setup_integration(hass, config_entry, [])

    result = await config_entry.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-email",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": expected_error})
    nice_go.authenticate.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "test-email",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(len(hass.config_entries.async_entries())).to_equal(1)
