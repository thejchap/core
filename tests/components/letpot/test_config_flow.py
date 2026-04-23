"""Test the LetPot config flow."""

import dataclasses
from typing import Any
from unittest.mock import AsyncMock

from letpot.exceptions import LetPotAuthenticationException, LetPotConnectionException
from tryke import Depends, expect, fixture, test

from homeassistant.components.letpot.const import (
    CONF_ACCESS_TOKEN_EXPIRES,
    CONF_REFRESH_TOKEN,
    CONF_REFRESH_TOKEN_EXPIRES,
    CONF_USER_ID,
    DOMAIN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import AUTHENTICATION
from ._fixtures import mock_client, mock_config_entry, mock_setup_entry

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network


@fixture
def _trigger_executor(_mn: None = Depends(mock_network)) -> None:
    """Trigger the hook executor path."""
    return None


def _assert_result_success(result: Any) -> None:
    """Assert successful end of flow result, creating an entry."""
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(AUTHENTICATION.email)
    expect(result["data"]).to_equal(
        {
            CONF_ACCESS_TOKEN: AUTHENTICATION.access_token,
            CONF_ACCESS_TOKEN_EXPIRES: AUTHENTICATION.access_token_expires,
            CONF_REFRESH_TOKEN: AUTHENTICATION.refresh_token,
            CONF_REFRESH_TOKEN_EXPIRES: AUTHENTICATION.refresh_token_expires,
            CONF_USER_ID: AUTHENTICATION.user_id,
            CONF_EMAIL: AUTHENTICATION.email,
        }
    )
    expect(result["result"].unique_id).to_equal(AUTHENTICATION.user_id)


@test
async def full_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_client: AsyncMock = Depends(mock_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test full flow with success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "email@example.com",
            CONF_PASSWORD: "test-password",
        },
    )

    _assert_result_success(result)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test.cases(
    test.case("invalid_auth", LetPotAuthenticationException, "invalid_auth"),
    test.case("cannot_connect", LetPotConnectionException, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def flow_exceptions(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test flow with exception during login and recovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    mock_client.login.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "email@example.com",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    mock_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "email@example.com",
            CONF_PASSWORD: "test-password",
        },
    )

    _assert_result_success(result)
    expect(len(mock_setup_entry.mock_calls)).to_equal(1)


@test
async def flow_duplicate(
    hass: HomeAssistant = Depends(hass_fixture),
    _mock_client: AsyncMock = Depends(mock_client),
    mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test flow aborts when trying to add a previously added account."""
    mock_config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(result["errors"]).to_equal({})

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "email@example.com",
            CONF_PASSWORD: "test-password",
        },
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(len(mock_setup_entry.mock_calls)).to_equal(0)


@test
async def reauth_flow(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow with success."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    updated_auth = dataclasses.replace(
        AUTHENTICATION,
        access_token="new_access_token",
        refresh_token="new_refresh_token",
    )
    mock_client.login.return_value = updated_auth
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data).to_equal(
        {
            CONF_ACCESS_TOKEN: "new_access_token",
            CONF_ACCESS_TOKEN_EXPIRES: AUTHENTICATION.access_token_expires,
            CONF_REFRESH_TOKEN: "new_refresh_token",
            CONF_REFRESH_TOKEN_EXPIRES: AUTHENTICATION.refresh_token_expires,
            CONF_USER_ID: AUTHENTICATION.user_id,
            CONF_EMAIL: AUTHENTICATION.email,
        }
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test.cases(
    test.case("invalid_auth", LetPotAuthenticationException, "invalid_auth"),
    test.case("cannot_connect", LetPotConnectionException, "cannot_connect"),
    test.case("unknown", Exception, "unknown"),
)
async def reauth_exceptions(
    exception: type[Exception],
    error: str,
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow with exception during login and recovery."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    mock_client.login.side_effect = exception
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password"},
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    updated_auth = dataclasses.replace(
        AUTHENTICATION,
        access_token="new_access_token",
        refresh_token="new_refresh_token",
    )
    mock_client.login.return_value = updated_auth
    mock_client.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data).to_equal(
        {
            CONF_ACCESS_TOKEN: "new_access_token",
            CONF_ACCESS_TOKEN_EXPIRES: AUTHENTICATION.access_token_expires,
            CONF_REFRESH_TOKEN: "new_refresh_token",
            CONF_REFRESH_TOKEN_EXPIRES: AUTHENTICATION.refresh_token_expires,
            CONF_USER_ID: AUTHENTICATION.user_id,
            CONF_EMAIL: AUTHENTICATION.email,
        }
    )
    expect(len(hass.config_entries.async_entries())).to_equal(1)


@test
async def reauth_different_user_id_new(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow with different, new user ID updating the existing entry."""
    mock_config_entry.add_to_hass(hass)
    config_entries = hass.config_entries.async_entries()
    expect(len(config_entries)).to_equal(1)
    expect(config_entries[0].unique_id).to_equal(AUTHENTICATION.user_id)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    updated_auth = dataclasses.replace(AUTHENTICATION, user_id="new_user_id")
    mock_client.login.return_value = updated_auth
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    expect(mock_config_entry.data).to_equal(
        {
            CONF_ACCESS_TOKEN: AUTHENTICATION.access_token,
            CONF_ACCESS_TOKEN_EXPIRES: AUTHENTICATION.access_token_expires,
            CONF_REFRESH_TOKEN: AUTHENTICATION.refresh_token,
            CONF_REFRESH_TOKEN_EXPIRES: AUTHENTICATION.refresh_token_expires,
            CONF_USER_ID: "new_user_id",
            CONF_EMAIL: AUTHENTICATION.email,
        }
    )
    config_entries = hass.config_entries.async_entries()
    expect(len(config_entries)).to_equal(1)
    expect(config_entries[0].unique_id).to_equal("new_user_id")


@test
async def reauth_different_user_id_existing(
    hass: HomeAssistant = Depends(hass_fixture),
    mock_client: AsyncMock = Depends(mock_client),
    _mock_setup_entry: AsyncMock = Depends(mock_setup_entry),
    mock_config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauth flow with different, existing user ID aborting."""
    mock_config_entry.add_to_hass(hass)
    mock_other = MockConfigEntry(
        domain=DOMAIN, title="email2@example.com", data={}, unique_id="other_user_id"
    )
    mock_other.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    updated_auth = dataclasses.replace(AUTHENTICATION, user_id="other_user_id")
    mock_client.login.return_value = updated_auth
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "new-password"},
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")
    expect(len(hass.config_entries.async_entries())).to_equal(2)
