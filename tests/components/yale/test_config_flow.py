"""Test the yale config flow."""

from unittest.mock import ANY, Mock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.yale.application_credentials import (
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)
from homeassistant.components.yale.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    client_credentials,
    disable_ratelimit_checks,
    jwt,
    mock_config_entry,
    mock_discovery,
    reauth_jwt,
    reauth_jwt_wrong_account,
    skip_cloud,
)
from .mocks import USER_ID

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

CLIENT_ID = "1"


@fixture
def mock_setup_entry():
    """Patch async_setup_entry."""
    with patch(
        "homeassistant.components.yale.async_setup_entry", return_value=True
    ) as mock_setup_entry:
        yield mock_setup_entry


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _credentials: None = Depends(client_credentials),
    _request: None = Depends(current_request_with_host),
    _discovery: object = Depends(mock_discovery),
    _ratelimit: None = Depends(disable_ratelimit_checks),
    _cloud: None = Depends(skip_cloud),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    jwt: str = Depends(jwt),
    setup_entry: Mock = Depends(mock_setup_entry),
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

    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
    )

    auth_client = await client()
    resp = await auth_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": jwt,
            "scope": "any",
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "user_id": "mock-user-id",
            "expires_at": 1697753347,
        },
    )

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)
    entry = hass.config_entries.async_entries(DOMAIN)[0]
    expect(entry.unique_id).to_equal(USER_ID)

    expect(result2["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result2["result"].unique_id).to_equal(USER_ID)
    expect(entry.data).to_equal(
        {
            "auth_implementation": "yale",
            "token": {
                "access_token": jwt,
                "expires_at": ANY,
                "expires_in": ANY,
                "refresh_token": "mock-refresh-token",
                "scope": "any",
                "user_id": "mock-user-id",
            },
        }
    )


@test
async def full_flow_already_exists(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    jwt: str = Depends(jwt),
    _setup_entry: Mock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Check full flow for a user that already exists."""
    config_entry.add_to_hass(hass)

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

    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
    )

    auth_client = await client()
    resp = await auth_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": jwt,
            "scope": "any",
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "user_id": "mock-user-id",
            "expires_at": 1697753347,
        },
    )

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    reauth_jwt: str = Depends(reauth_jwt),
    _setup_entry: Mock = Depends(mock_setup_entry),
) -> None:
    """Test the reauthentication case updates the existing config entry."""
    config_entry.add_to_hass(hass)

    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    result = flows[0]
    expect(result["step_id"]).to_equal("auth")

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    auth_client = await client()
    resp = await auth_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": reauth_jwt,
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "user_id": USER_ID,
            "token_type": "Bearer",
            "expires_at": 1697753347,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")

    expect(config_entry.unique_id).to_equal(USER_ID)
    expect("token" in config_entry.data).to_be(True)
    expect(config_entry.data["token"]["access_token"]).to_equal(reauth_jwt)


@test
async def reauth_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    reauth_jwt_wrong_account: str = Depends(reauth_jwt_wrong_account),
    jwt: str = Depends(jwt),
    _setup_entry: Mock = Depends(mock_setup_entry),
) -> None:
    """Test the reauthentication aborts if user tries to reauthenticate with another account."""
    expect(config_entry.data["token"]["access_token"]).to_equal(jwt)

    config_entry.add_to_hass(hass)

    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    result = flows[0]
    expect(result["step_id"]).to_equal("auth")

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    auth_client = await client()
    resp = await auth_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": reauth_jwt_wrong_account,
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "token_type": "Bearer",
            "expires_at": 1697753347,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_invalid_user")

    expect(config_entry.unique_id).to_equal(USER_ID)
    expect("token" in config_entry.data).to_be(True)
    expect(config_entry.data["token"]["access_token"]).to_equal(jwt)
