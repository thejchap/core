"""Tests for config flow."""

from unittest.mock import AsyncMock, patch

from microBeesPy import MicroBeesException
from tryke import Depends, expect, fixture, test

from homeassistant.components.microbees.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from . import setup_integration
from ._fixtures import (
    CLIENT_ID,
    MICROBEES_AUTH_URI,
    MICROBEES_TOKEN_URI,
    SCOPES,
    config_entry,
    microbees,
    setup_credentials,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    aioclient_mock,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import ClientSessionGenerator


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _request: None = Depends(current_request_with_host),
    _credentials: None = Depends(setup_credentials),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth_fn: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock_fn: AiohttpClientMocker = Depends(aioclient_mock),
    microbees_mock: AsyncMock = Depends(microbees),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)
    expect(result["url"]).to_equal(
        f"{MICROBEES_AUTH_URI}?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        f"&scope={'+'.join(SCOPES)}"
    )

    client = await hass_client_no_auth_fn()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")
    aioclient_mock_fn.clear_requests()
    aioclient_mock_fn.post(
        MICROBEES_TOKEN_URI,
        json={
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "refresh_token": "mock-refresh-token",
            "expires_in": 99999,
            "scope": " ".join(SCOPES),
            "client_id": CLIENT_ID,
        },
    )

    with patch(
        "homeassistant.components.microbees.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("test@microbees.com")
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal("54321")
    expect("token" in result["result"].data).to_be(True)
    expect(result["result"].data["token"]["access_token"]).to_equal("mock-access-token")
    expect(result["result"].data["token"]["refresh_token"]).to_equal(
        "mock-refresh-token"
    )


@test
async def config_non_unique_profile(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth_fn: ClientSessionGenerator = Depends(hass_client_no_auth),
    microbees_mock: AsyncMock = Depends(microbees),
    config_entry_obj: MockConfigEntry = Depends(config_entry),
    aioclient_mock_fn: AiohttpClientMocker = Depends(aioclient_mock),
) -> None:
    """Test setup a non-unique profile."""
    await setup_integration(hass, config_entry_obj)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)
    expect(result["url"]).to_equal(
        f"{MICROBEES_AUTH_URI}?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        f"&scope={'+'.join(SCOPES)}"
    )

    client = await hass_client_no_auth_fn()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock_fn.clear_requests()
    aioclient_mock_fn.post(
        MICROBEES_TOKEN_URI,
        json={
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "refresh_token": "mock-refresh-token",
            "expires_in": 99999,
            "scope": " ".join(SCOPES),
            "client_id": CLIENT_ID,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def config_reauth_profile(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth_fn: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock_fn: AiohttpClientMocker = Depends(aioclient_mock),
    config_entry_obj: MockConfigEntry = Depends(config_entry),
    microbees_mock: AsyncMock = Depends(microbees),
) -> None:
    """Test reauth an existing profile reauthenticates the config entry."""
    await setup_integration(hass, config_entry_obj)

    result = await config_entry_obj.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    expect(result["url"]).to_equal(
        f"{MICROBEES_AUTH_URI}?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        f"&scope={'+'.join(SCOPES)}"
    )
    client = await hass_client_no_auth_fn()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock_fn.clear_requests()
    aioclient_mock_fn.post(
        MICROBEES_TOKEN_URI,
        json={
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "refresh_token": "mock-refresh-token",
            "expires_in": 99999,
            "scope": " ".join(SCOPES),
            "client_id": CLIENT_ID,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(bool(result)).to_be(True)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def config_reauth_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth_fn: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock_fn: AiohttpClientMocker = Depends(aioclient_mock),
    config_entry_obj: MockConfigEntry = Depends(config_entry),
    microbees_mock: AsyncMock = Depends(microbees),
) -> None:
    """Test reauth with wrong account."""
    await setup_integration(hass, config_entry_obj)
    microbees_mock.return_value.getMyProfile.return_value.id = "12345"
    result = await config_entry_obj.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    expect(result["url"]).to_equal(
        f"{MICROBEES_AUTH_URI}?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        f"&scope={'+'.join(SCOPES)}"
    )
    client = await hass_client_no_auth_fn()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock_fn.clear_requests()
    aioclient_mock_fn.post(
        MICROBEES_TOKEN_URI,
        json={
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "refresh_token": "mock-refresh-token",
            "expires_in": 99999,
            "scope": " ".join(SCOPES),
            "client_id": CLIENT_ID,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(bool(result)).to_be(True)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_account")


@test
async def config_flow_with_invalid_credentials(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth_fn: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock_fn: AiohttpClientMocker = Depends(aioclient_mock),
    microbees_mock: AsyncMock = Depends(microbees),
) -> None:
    """Test flow with invalid credentials."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)
    expect(result["url"]).to_equal(
        f"{MICROBEES_AUTH_URI}?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        f"&scope={'+'.join(SCOPES)}"
    )

    client = await hass_client_no_auth_fn()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock_fn.clear_requests()
    aioclient_mock_fn.post(
        MICROBEES_TOKEN_URI,
        json={
            "status": 401,
            "error": "Invalid Params: invalid client id/secret",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(bool(result)).to_be(True)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("oauth_error")


@test.cases(
    test.case(
        "invalid_auth",
        exception=MicroBeesException("Invalid auth"),
        error="invalid_auth",
    ),
    test.case(
        "unknown",
        exception=Exception("Unexpected error"),
        error="unknown",
    ),
)
async def unexpected_exceptions(
    *,
    exception: Exception,
    error: str,
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth_fn: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock_fn: AiohttpClientMocker = Depends(aioclient_mock),
    config_entry_obj: MockConfigEntry = Depends(config_entry),
    microbees_mock: AsyncMock = Depends(microbees),
) -> None:
    """Test unknown error from server."""
    await setup_integration(hass, config_entry_obj)
    microbees_mock.return_value.getMyProfile.side_effect = exception

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)
    expect(result["url"]).to_equal(
        f"{MICROBEES_AUTH_URI}?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        f"&scope={'+'.join(SCOPES)}"
    )

    client = await hass_client_no_auth_fn()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")
    aioclient_mock_fn.clear_requests()
    aioclient_mock_fn.post(
        MICROBEES_TOKEN_URI,
        json={
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "refresh_token": "mock-refresh-token",
            "expires_in": 99999,
            "scope": " ".join(SCOPES),
            "client_id": CLIENT_ID,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(bool(result)).to_be(True)
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(error)
