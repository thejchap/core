"""Test the Dropbox config flow."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

from tryke import Depends, expect, fixture, test
from yarl import URL

from homeassistant import config_entries
from homeassistant.components.dropbox.const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_SCOPES,
    OAUTH2_TOKEN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    ACCOUNT_EMAIL,
    ACCOUNT_ID,
    CLIENT_ID,
    mock_config_entry,
    mock_dropbox_client,
    mock_setup_entry,
    setup_credentials,
)

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    aioclient_mock as aioclient_mock_fx,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _credentials: None = Depends(setup_credentials),
    _request: None = Depends(current_request_with_host),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_fn: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _client: MagicMock = Depends(mock_dropbox_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test creating a new config entry through the OAuth flow."""
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

    result_url = URL(result["url"])
    expect(f"{result_url.origin()}{result_url.path}").to_equal(OAUTH2_AUTHORIZE)
    expect(result_url.query["response_type"]).to_equal("code")
    expect(result_url.query["client_id"]).to_equal(CLIENT_ID)
    expect(result_url.query["redirect_uri"]).to_equal(
        "https://example.com/auth/external/callback"
    )
    expect(result_url.query["state"]).to_equal(state)
    expect(result_url.query["scope"]).to_equal(" ".join(OAUTH2_SCOPES))
    expect(result_url.query["token_access_type"]).to_equal("offline")
    expect(bool(result_url.query["code_challenge"])).to_be(True)
    expect(result_url.query["code_challenge_method"]).to_equal("S256")

    cli = await client_fn()
    resp = await cli.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 60,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal(ACCOUNT_EMAIL)
    expect(result["data"]["token"]["access_token"]).to_equal("mock-access-token")
    expect(result["result"].unique_id).to_equal(ACCOUNT_ID)
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def already_configured(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_fn: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: MagicMock = Depends(mock_dropbox_client),
) -> None:
    """Test aborting when the account is already configured."""
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

    cli = await client_fn()
    resp = await cli.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "token_type": "Bearer",
            "expires_in": 60,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "success",
        new_account_info=SimpleNamespace(account_id=ACCOUNT_ID, email=ACCOUNT_EMAIL),
        expected_reason="reauth_successful",
        expected_setup_calls=1,
        expected_access_token="updated-access-token",
    ),
    test.case(
        "wrong_account",
        new_account_info=SimpleNamespace(
            account_id="dbid:different", email="other@example.com"
        ),
        expected_reason="wrong_account",
        expected_setup_calls=0,
        expected_access_token="mock-access-token",
    ),
)
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_fn: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    dropbox_client: MagicMock = Depends(mock_dropbox_client),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    *,
    new_account_info: SimpleNamespace,
    expected_reason: str,
    expected_setup_calls: int,
    expected_access_token: str,
) -> None:
    """Test reauthentication flow outcomes."""
    config_entry.add_to_hass(hass)

    dropbox_client.get_account_info.return_value = new_account_info

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

    cli = await client_fn()
    resp = await cli.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "updated-access-token",
            "token_type": "Bearer",
            "expires_in": 120,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(expected_reason)
    expect(setup_entry.await_count).to_equal(expected_setup_calls)

    expect(config_entry.data["token"]["access_token"]).to_equal(expected_access_token)
