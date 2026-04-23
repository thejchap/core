"""Test the Nintendo Switch parental controls config flow."""

from __future__ import annotations

from unittest.mock import AsyncMock

from pynintendoauth.exceptions import HttpException, InvalidSessionTokenException
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.nintendo_parental_controls.const import (
    CONF_SESSION_TOKEN,
    DOMAIN,
)
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from tests.common import MockConfigEntry
from tests.components.nintendo_parental_controls._fixtures import (
    mock_config_entry,
    mock_nintendo_api,
    mock_nintendo_authenticator,
    mock_setup_entry,
)
from tests.components.nintendo_parental_controls.const import (
    ACCOUNT_ID,
    API_TOKEN,
    LOGIN_URL,
)
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_net: None = Depends(mock_network)) -> None:
    """Wire mock_network for every test."""


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mse: AsyncMock = Depends(mock_setup_entry),
    _auth: AsyncMock = Depends(mock_nintendo_authenticator),
    _api: AsyncMock = Depends(mock_nintendo_api),
) -> None:
    """Test a full and successful config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result is not None).to_be(True)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("link" in result["description_placeholders"]).to_be(True)
    expect(result["description_placeholders"]["link"]).to_equal(LOGIN_URL)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(ACCOUNT_ID)
    expect(result["data"][CONF_SESSION_TOKEN]).to_equal(API_TOKEN)
    expect(result["result"].unique_id).to_equal(ACCOUNT_ID)


@test
async def already_configured(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _auth: AsyncMock = Depends(mock_nintendo_authenticator),
    _api: AsyncMock = Depends(mock_nintendo_api),
) -> None:
    """Test that the flow aborts if the account is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def invalid_auth(
    hass: HomeAssistant = Depends(hass_fixture),
    auth: AsyncMock = Depends(mock_nintendo_authenticator),
    _api: AsyncMock = Depends(mock_nintendo_api),
) -> None:
    """Test handling of invalid authentication."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result is not None).to_be(True)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("link" in result["description_placeholders"]).to_be(True)

    auth.async_complete_login.side_effect = InvalidSessionTokenException(
        status_code=401, message="Test"
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "invalid_token"}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    auth.async_complete_login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(ACCOUNT_ID)
    expect(result["data"][CONF_SESSION_TOKEN]).to_equal(API_TOKEN)
    expect(result["result"].unique_id).to_equal(ACCOUNT_ID)


@test
async def missing_devices(
    hass: HomeAssistant = Depends(hass_fixture),
    auth: AsyncMock = Depends(mock_nintendo_authenticator),
    api: AsyncMock = Depends(mock_nintendo_api),
) -> None:
    """Test handling of no devices found."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result is not None).to_be(True)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("link" in result["description_placeholders"]).to_be(True)

    auth.async_complete_login.side_effect = None
    api.async_get_account_devices.side_effect = HttpException(
        status_code=404, message="TEST"
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("no_devices_found")


@test
async def cannot_connect(
    hass: HomeAssistant = Depends(hass_fixture),
    auth: AsyncMock = Depends(mock_nintendo_authenticator),
    api: AsyncMock = Depends(mock_nintendo_api),
) -> None:
    """Test handling of connection errors during device discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result is not None).to_be(True)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect("link" in result["description_placeholders"]).to_be(True)

    auth.async_complete_login.side_effect = None
    api.async_get_account_devices.side_effect = HttpException(
        status_code=500, message="TEST"
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({"base": "cannot_connect"})

    api.async_get_account_devices.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(ACCOUNT_ID)
    expect(result["data"][CONF_SESSION_TOKEN]).to_equal(API_TOKEN)
    expect(result["result"].unique_id).to_equal(ACCOUNT_ID)


@test
async def reauthentication_success(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _auth: AsyncMock = Depends(mock_nintendo_authenticator),
) -> None:
    """Test successful reauthentication."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def reauthentication_fail(
    hass: HomeAssistant = Depends(hass_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    auth: AsyncMock = Depends(mock_nintendo_authenticator),
) -> None:
    """Test failed reauthentication."""
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    auth.async_complete_login.side_effect = InvalidSessionTokenException(
        status_code=401, message="Test"
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["errors"]).to_equal({"base": "invalid_auth"})

    auth.async_complete_login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: API_TOKEN}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
