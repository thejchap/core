"""Config flow tests for the Actron Air Integration."""

import asyncio
from unittest.mock import AsyncMock

from actron_neo_api import ActronAirAuthError
from actron_neo_api.models.auth import ActronAirUserInfo
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.actron_air.const import DOMAIN
from homeassistant.const import CONF_API_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from ._fixtures import mock_actron_api, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def user_flow_oauth2_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_actron_api),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful OAuth2 device code flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
    expect(result["step_id"]).to_equal("user")
    expect(result["progress_action"]).to_equal("wait_for_authorization")
    expect(result["description_placeholders"] is not None).to_be(True)
    expect("user_code" in result["description_placeholders"]).to_be(True)
    expect(result["description_placeholders"]["user_code"]).to_equal("ABC123")

    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test@example.com")
    expect(result["data"]).to_equal(
        {
            CONF_API_TOKEN: "test_refresh_token",
        }
    )
    expect(result["result"].unique_id).to_equal("test_user_id")


@test
async def user_flow_oauth2_pending(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    actron_api: AsyncMock = Depends(mock_actron_api),
) -> None:
    """Test OAuth2 flow when authorization is still pending."""

    async def hang_forever(device_code: str) -> None:
        await asyncio.Event().wait()

    actron_api.poll_for_token = hang_forever

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
    expect(result["step_id"]).to_equal("user")
    expect(result["progress_action"]).to_equal("wait_for_authorization")
    expect(result["description_placeholders"] is not None).to_be(True)
    expect("user_code" in result["description_placeholders"]).to_be(True)
    expect(result["description_placeholders"]["user_code"]).to_equal("ABC123")


@test
async def user_flow_oauth2_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    actron_api: AsyncMock = Depends(mock_actron_api),
) -> None:
    """Test OAuth2 flow with authentication error during device code request."""
    actron_api.request_device_code = AsyncMock(
        side_effect=ActronAirAuthError("OAuth2 error")
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("oauth2_error")


@test
async def user_flow_token_polling_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    actron_api: AsyncMock = Depends(mock_actron_api),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test OAuth2 flow with error during token polling."""
    actron_api.poll_for_token = AsyncMock(
        side_effect=ActronAirAuthError("Token polling error")
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS_DONE)
    expect(result["step_id"]).to_equal("connection_error")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("connection_error")

    async def successful_poll_for_token(device_code: str) -> dict[str, str]:
        await asyncio.sleep(0.1)
        return {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

    actron_api.poll_for_token = successful_poll_for_token

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
    expect(result["step_id"]).to_equal("user")
    expect(result["progress_action"]).to_equal("wait_for_authorization")

    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test@example.com")
    expect(result["data"]).to_equal(
        {
            CONF_API_TOKEN: "test_refresh_token",
        }
    )
    expect(result["result"].unique_id).to_equal("test_user_id")


@test
async def user_flow_duplicate_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_actron_api),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test duplicate account handling - should abort when same account is already configured."""
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
    expect(result["step_id"]).to_equal("user")
    expect(result["progress_action"]).to_equal("wait_for_authorization")
    expect(result["description_placeholders"] is not None).to_be(True)
    expect("user_code" in result["description_placeholders"]).to_be(True)
    expect(result["description_placeholders"]["user_code"]).to_equal("ABC123")

    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def reauth_flow_success(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _api: AsyncMock = Depends(mock_actron_api),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test successful reauthentication flow."""
    config_entry.add_to_hass(hass)
    existing_entry = config_entry

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
    expect(result["step_id"]).to_equal("user")
    expect(result["progress_action"]).to_equal("wait_for_authorization")

    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(existing_entry.data[CONF_API_TOKEN]).to_equal("test_refresh_token")


@test
async def reauth_flow_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    actron_api: AsyncMock = Depends(mock_actron_api),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication flow with wrong account."""
    config_entry.add_to_hass(hass)

    actron_api.get_user_info = AsyncMock(
        return_value=ActronAirUserInfo(
            id="different_user_id", email="different@example.com"
        )
    )

    result = await config_entry.start_reauth_flow(hass)

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
    expect(result["step_id"]).to_equal("user")
    expect(result["progress_action"]).to_equal("wait_for_authorization")

    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_account")


@test
async def user_flow_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    actron_api: AsyncMock = Depends(mock_actron_api),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test OAuth2 flow when login task raises a non-CannotConnect exception."""

    async def raise_generic_error(device_code: str) -> None:
        raise RuntimeError("Unexpected error")

    actron_api.poll_for_token = raise_generic_error

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS_DONE)
    expect(result["step_id"]).to_equal("timeout")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("timeout")

    async def successful_poll_for_token(device_code: str) -> dict[str, str]:
        await asyncio.sleep(0.1)
        return {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
        }

    actron_api.poll_for_token = successful_poll_for_token

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    expect(result["type"]).to_be(FlowResultType.SHOW_PROGRESS)
    expect(result["step_id"]).to_equal("user")
    expect(result["progress_action"]).to_equal("wait_for_authorization")

    await hass.async_block_till_done()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test@example.com")


@test
async def finish_login_auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    actron_api: AsyncMock = Depends(mock_actron_api),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test finish_login step when get_user_info raises ActronAirAuthError."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    await hass.async_block_till_done()

    actron_api.get_user_info = AsyncMock(
        side_effect=ActronAirAuthError("Auth error getting user info")
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("oauth2_error")
