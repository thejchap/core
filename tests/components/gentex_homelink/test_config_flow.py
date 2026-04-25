"""Test the homelink config flow."""

from http import HTTPStatus
from unittest.mock import AsyncMock

import botocore.exceptions
from tryke import Depends, expect, fixture, test

from homeassistant.components.gentex_homelink.const import DOMAIN, OAUTH2_TOKEN_URL
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from . import (
    INVALID_TEST_ACCESS_JWT,
    INVALID_TEST_CREDENTIALS,
    TEST_ACCESS_JWT,
    TEST_CREDENTIALS,
    TEST_UNIQUE_ID,
    setup_integration,
)
from ._fixtures import (
    aioclient_mock_post_token,
    mock_config_entry,
    mock_setup_entry,
    mock_srp_auth,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import hass as hass_fixture, mock_network
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(_network: None = Depends(mock_network)) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _srp: AsyncMock = Depends(mock_srp_auth),
    _setup: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_CREDENTIALS,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["data"]).to_equal(
        {
            "auth_implementation": "gentex_homelink",
            "token": {
                "access_token": TEST_ACCESS_JWT,
                "refresh_token": "refresh",
                "expires_in": 3600,
                "token_type": "bearer",
                "expires_at": result["data"]["token"]["expires_at"],
            },
        }
    )
    expect(result["result"].unique_id).to_equal(TEST_UNIQUE_ID)
    expect(result["title"]).to_equal("HomeLink")


@test
async def unique_configurations(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _srp: AsyncMock = Depends(mock_srp_auth),
    _setup: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Check full flow."""
    await setup_integration(hass, config_entry)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("user")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_CREDENTIALS,
    )
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "srp_auth_failed",
        exception=botocore.exceptions.ClientError({"Error": {}}, "Some operation"),
        error="srp_auth_failed",
    ),
    test.case(
        "unknown",
        exception=Exception("Some error"),
        error="unknown",
    ),
)
async def exceptions(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    srp_auth: AsyncMock = Depends(mock_srp_auth),
    _setup: AsyncMock = Depends(mock_setup_entry),
    *,
    exception: Exception,
    error: str,
) -> None:
    """Test exceptions are handled correctly."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    srp_auth.async_get_access_token.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_CREDENTIALS,
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["errors"]).to_equal({"base": error})

    srp_auth.async_get_access_token.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_CREDENTIALS,
    )
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def auth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _srp: AsyncMock = Depends(mock_srp_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_post_token),
) -> None:
    """Test if the auth server returns an error refreshing the token."""
    aioclient_mock.clear_requests()
    aioclient_mock.post(OAUTH2_TOKEN_URL, status=HTTPStatus.UNAUTHORIZED)

    expect(len(aioclient_mock.mock_calls)).to_equal(0)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={"email": "test@test.com", "password": "SomePassword"},
    )
    expect(len(aioclient_mock.mock_calls)).to_equal(1)
    expect(aioclient_mock.mock_calls[0][0]).to_equal("POST")
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)


@test
async def reauth_successful(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _srp: AsyncMock = Depends(mock_srp_auth),
    _aio: AiohttpClientMocker = Depends(aioclient_mock_post_token),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reauth flow."""
    await setup_integration(hass, config_entry)
    result = await config_entry.start_reauth_flow(hass)
    expect(result["step_id"]).to_equal("reauth_confirm")
    expect(result["type"]).to_be(FlowResultType.FORM)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=TEST_CREDENTIALS,
    )
    expect(result["reason"]).to_equal("reauth_successful")
    expect(result["type"]).to_be(FlowResultType.ABORT)


@fixture
def invalid_srp_token() -> str:
    """Return invalid JWT for reauth_error."""
    return INVALID_TEST_ACCESS_JWT


@test
async def reauth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _aio: AiohttpClientMocker = Depends(aioclient_mock_post_token),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    invalid_jwt: str = Depends(invalid_srp_token),
) -> None:
    """Test the reauth flow with mismatched unique id."""
    # Manually patch SRPAuth with the invalid JWT for this test
    from unittest.mock import patch as _patch

    with _patch(
        "homeassistant.components.gentex_homelink.config_flow.SRPAuth"
    ) as mock_srp:
        instance = mock_srp.return_value
        instance.async_get_access_token.return_value = {
            "AuthenticationResult": {
                "AccessToken": invalid_jwt,
                "RefreshToken": "refresh",
                "TokenType": "bearer",
                "ExpiresIn": 3600,
            }
        }

        await setup_integration(hass, config_entry)
        result = await config_entry.start_reauth_flow(hass)
        expect(result["step_id"]).to_equal("reauth_confirm")
        expect(result["type"]).to_be(FlowResultType.FORM)
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=INVALID_TEST_CREDENTIALS,
        )
        expect(result["reason"]).to_equal("unique_id_mismatch")
        expect(result["type"]).to_be(FlowResultType.ABORT)
