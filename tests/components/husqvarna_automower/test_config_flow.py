"""Test the Husqvarna Automower config flow."""

from unittest.mock import AsyncMock, patch

from aioautomower.const import API_BASE_URL
from aioautomower.session import AutomowerEndpoint
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.husqvarna_automower.const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from . import setup_integration
from ._fixtures import jwt, mock_automower_client, mock_config_entry, setup_credentials
from .const import CLIENT_ID, USER_ID

from tests.common import MockConfigEntry, async_load_fixture
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


@test.cases(
    test.case(
        "ok",
        new_scope="iam:read amc:api",
        fixture="mower.json",
        exception=None,
        amount=1,
    ),
    test.case(
        "exc",
        new_scope="iam:read amc:api",
        fixture="mower.json",
        exception=Exception,
        amount=0,
    ),
    test.case(
        "missing_scope",
        new_scope="iam:read",
        fixture="mower.json",
        exception=None,
        amount=0,
    ),
    test.case(
        "empty",
        new_scope="iam:read amc:api",
        fixture="empty.json",
        exception=None,
        amount=0,
    ),
)
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    jwt: str = Depends(jwt),
    *,
    new_scope: str,
    amount: int,
    fixture: str,
    exception: type[Exception] | None,
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        "husqvarna_automower", context={"source": config_entries.SOURCE_USER}
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

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": jwt,
            "scope": new_scope,
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "provider": "husqvarna",
            "user_id": "mock-user-id",
            "token_type": "Bearer",
            "expires_at": 1697753347,
        },
    )
    aioclient_mock.get(
        f"{API_BASE_URL}/{AutomowerEndpoint.mowers}",
        text=await async_load_fixture(hass, fixture, DOMAIN),
        exc=exception,
    )
    with patch(
        "homeassistant.components.husqvarna_automower.async_setup_entry",
        return_value=True,
    ) as mock_setup:
        await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(amount)
    expect(len(mock_setup.mock_calls)).to_equal(amount)


@test
async def config_non_unique_profile(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _client: AsyncMock = Depends(mock_automower_client),
    jwt: str = Depends(jwt),
) -> None:
    """Test setup a non-unique profile."""
    await setup_integration(hass, config_entry)
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
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": jwt,
            "scope": "iam:read amc:api",
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "provider": "husqvarna",
            "user_id": USER_ID,
            "token_type": "Bearer",
            "expires_at": 1697753347,
        },
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test.cases(
    test.case(
        "reauth_full",
        scope="iam:read amc:api",
        step_id="reauth_confirm",
        reason="reauth_successful",
        new_scope="iam:read amc:api",
    ),
    test.case(
        "missing_to_full",
        scope="iam:read",
        step_id="missing_scope",
        reason="reauth_successful",
        new_scope="iam:read amc:api",
    ),
    test.case(
        "missing_to_missing",
        scope="iam:read",
        step_id="missing_scope",
        reason="missing_amc_scope",
        new_scope="iam:read",
    ),
)
async def reauth(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_automower_client),
    jwt: str = Depends(jwt),
    *,
    scope: str,
    step_id: str,
    new_scope: str,
    reason: str,
) -> None:
    """Test the reauthentication case updates the existing config entry."""
    config_entry.data["token"]["scope"] = scope
    config_entry.add_to_hass(hass)

    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    result = flows[0]
    expect(result["step_id"]).to_equal(step_id)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
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
    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": "mock-updated-token",
            "scope": new_scope,
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "provider": "husqvarna",
            "user_id": USER_ID,
            "token_type": "Bearer",
            "expires_at": 1697753347,
        },
    )

    with patch(
        "homeassistant.components.husqvarna_automower.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal(reason)

    expect(config_entry.unique_id).to_equal(USER_ID)
    expect("token" in config_entry.data).to_be(True)
    expect(config_entry.data["token"].get("access_token")).to_equal(
        "mock-updated-token"
    )
    expect(config_entry.data["token"].get("refresh_token")).to_equal(
        "mock-refresh-token"
    )


@test
async def reauth_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    _client: AsyncMock = Depends(mock_automower_client),
    jwt: str = Depends(jwt),
) -> None:
    """Test the reauthentication aborts, if user tries to reauthenticate with another account."""
    config_entry.add_to_hass(hass)

    config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    result = flows[0]
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
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
    )
    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": "mock-updated-token",
            "scope": "iam:read amc:api",
            "expires_in": 86399,
            "refresh_token": "mock-refresh-token",
            "provider": "husqvarna",
            "user_id": "wrong_user_id",
            "token_type": "Bearer",
            "expires_at": 1697753347,
        },
    )

    with patch(
        "homeassistant.components.husqvarna_automower.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("wrong_account")

    expect(config_entry.unique_id).to_equal(USER_ID)
    expect("token" in config_entry.data).to_be(True)
    expect(config_entry.data["token"].get("access_token")).to_equal(jwt)
    expect(config_entry.data["token"].get("refresh_token")).to_equal(
        "3012bc9f-7a65-4240-b817-9154ffdcc30f"
    )
