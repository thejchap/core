"""Test the Watts Vision config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.watts.const import DOMAIN, OAUTH2_AUTHORIZE, OAUTH2_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    mock_config_entry,
    mock_setup_entry,
    setup_credentials,
    skip_cloud,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fx,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth as hass_client_no_auth_fx,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import ClientSessionGenerator


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _request: None = Depends(current_request_with_host),
    _skip_cloud: None = Depends(skip_cloud),
    _credentials: None = Depends(setup_credentials),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _setup: None = Depends(mock_setup_entry),
) -> None:
    """Test the full OAuth2 config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    expect(result.get("type")).to_be(FlowResultType.EXTERNAL_STEP)
    expect("url" in result).to_be(True)
    expect(OAUTH2_AUTHORIZE in result.get("url", "")).to_be(True)
    expect("response_type=code" in result.get("url", "")).to_be(True)
    expect("scope=" in result.get("url", "")).to_be(True)

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    with patch(
        "homeassistant.components.watts.config_flow.WattsVisionAuth.extract_user_id_from_token",
        return_value="user123",
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result.get("type")).to_be(FlowResultType.CREATE_ENTRY)
        expect(result.get("title")).to_equal("Watts Vision +")
        expect("token" in result.get("data", {})).to_be(True)
        expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
        expect(hass.config_entries.async_entries(DOMAIN)[0].unique_id).to_equal(
            "user123"
        )


@test
async def invalid_token_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test the OAuth2 config flow with invalid token."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "invalid-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    with patch(
        "homeassistant.components.watts.config_flow.WattsVisionAuth.extract_user_id_from_token",
        return_value=None,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        expect(result.get("type")).to_be(FlowResultType.ABORT)
        expect(result.get("reason")).to_equal("invalid_token")


@test
async def oauth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test OAuth error handling."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock.post(OAUTH2_TOKEN, json={"error": "invalid_grant"})

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("oauth_error")


@test
async def oauth_timeout(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test OAuth timeout handling."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock.post(OAUTH2_TOKEN, exc=TimeoutError())

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("oauth_timeout")


@test
async def oauth_invalid_response(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test OAuth invalid response handling."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock.post(OAUTH2_TOKEN, status=500, text="invalid json")

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("oauth_failed")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _setup: None = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reauthentication flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

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
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    with patch(
        "homeassistant.components.watts.config_flow.WattsVisionAuth.extract_user_id_from_token",
        return_value="test-user-id",
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    config_entry.data["token"].pop("expires_at")
    expect(dict(config_entry.data["token"])).to_equal(
        {
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
    )


@test
async def reauth_account_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reauthentication with a different account aborts."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

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
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    with patch(
        "homeassistant.components.watts.config_flow.WattsVisionAuth.extract_user_id_from_token",
        return_value="different-user-id",
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("account_mismatch")


@test
async def reconfigure_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _setup: None = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test the reconfiguration flow."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    with patch(
        "homeassistant.components.watts.config_flow.WattsVisionAuth.extract_user_id_from_token",
        return_value="test-user-id",
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reconfigure_successful")
    config_entry.data["token"].pop("expires_at")
    expect(dict(config_entry.data["token"])).to_equal(
        {
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
    )


@test
async def reconfigure_account_mismatch(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test reconfiguration with a different account aborts."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reconfigure_flow(hass)

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    with patch(
        "homeassistant.components.watts.config_flow.WattsVisionAuth.extract_user_id_from_token",
        return_value="different-user-id",
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("account_mismatch")


@test
async def unique_config_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fx),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Test that duplicate config entries are not allowed."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="user123",
    )
    config_entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 3600,
        },
    )

    with patch(
        "homeassistant.components.watts.config_flow.WattsVisionAuth.extract_user_id_from_token",
        return_value="user123",
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
