"""Test the myUplink config flow."""

from unittest.mock import patch

from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.myuplink.const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
)
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    access_token,
    expires_at,
    mock_config_entry,
    setup_credentials,
)
from .const import CLIENT_ID, UNIQUE_ID

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    aioclient_mock as aioclient_mock_fixture,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

REDIRECT_URL = "https://example.com/auth/external/callback"
CURRENT_SCOPE = "WRITESYSTEM READSYSTEM offline_access"


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _request: None = Depends(current_request_with_host),
    _credentials: None = Depends(setup_credentials),
) -> None:
    """Apply autouse-equivalent fixtures."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    token: str = Depends(access_token),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URL,
        },
    )

    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        f"&state={state}"
        f"&scope={CURRENT_SCOPE.replace(' ', '+')}"
    )

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": token,
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        f"homeassistant.components.{DOMAIN}.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)

    expect(result["data"]["auth_implementation"]).to_equal(DOMAIN)
    expect(result["data"]["token"]["refresh_token"]).to_equal("mock-refresh-token")
    expect(result["result"].unique_id).to_equal(UNIQUE_ID)


@test.cases(
    test.case(
        "reauth_only",
        unique_id=UNIQUE_ID,
        scope=CURRENT_SCOPE,
        expected_reason="reauth_successful",
    ),
    test.case(
        "account_mismatch",
        unique_id="wrong_uid",
        scope=CURRENT_SCOPE,
        expected_reason="account_mismatch",
    ),
    test.case(
        "wrong_scope",
        unique_id=UNIQUE_ID,
        scope="READSYSTEM offline_access",
        expected_reason="reauth_successful",
    ),
)
async def flow_reauth_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    token: str = Depends(access_token),
    expires_at_value: float = Depends(expires_at),
    *,
    unique_id: str,
    scope: str,
    expected_reason: str,
) -> None:
    """Test reauth step with correct params and mismatches."""
    current_token = {
        "auth_implementation": DOMAIN,
        "token": {
            "access_token": token,
            "scope": scope,
            "expires_in": 86399,
            "refresh_token": "3012bc9f-7a65-4240-b817-9154ffdcc30f",
            "token_type": "Bearer",
            "expires_at": expires_at_value,
        },
    }
    expect(
        bool(
            hass.config_entries.async_update_entry(
                config_entry, data=current_token, unique_id=unique_id
            )
        )
    ).to_be(True)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await config_entry.start_reauth_flow(hass)

    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    expect(result["step_id"]).to_equal("auth")

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URL,
        },
    )
    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        f"&state={state}"
        f"&scope={CURRENT_SCOPE.replace(' ', '+')}"
    )

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "updated-refresh-token",
            "access_token": token,
            "type": "Bearer",
            "expires_in": "60",
            "scope": CURRENT_SCOPE,
        },
    )

    with patch(
        f"homeassistant.components.{DOMAIN}.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        await hass.async_block_till_done()

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal(expected_reason)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test.cases(
    test.case(
        "reauth_only",
        unique_id=UNIQUE_ID,
        scope=CURRENT_SCOPE,
        expected_reason="reconfigure_successful",
    ),
    test.case(
        "account_mismatch",
        unique_id="wrong_uid",
        scope=CURRENT_SCOPE,
        expected_reason="account_mismatch",
    ),
)
async def flow_reconfigure_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_factory: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    token: str = Depends(access_token),
    expires_at_value: float = Depends(expires_at),
    *,
    unique_id: str,
    scope: str,
    expected_reason: str,
) -> None:
    """Test reconfigure step with correct params and mismatches."""
    current_token = {
        "auth_implementation": DOMAIN,
        "token": {
            "access_token": token,
            "scope": scope,
            "expires_in": 86399,
            "refresh_token": "3012bc9f-7a65-4240-b817-9154ffdcc30f",
            "token_type": "Bearer",
            "expires_at": expires_at_value,
        },
    }
    expect(
        bool(
            hass.config_entries.async_update_entry(
                config_entry, data=current_token, unique_id=unique_id
            )
        )
    ).to_be(True)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await config_entry.start_reconfigure_flow(hass)

    expect(result["step_id"]).to_equal("auth")

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URL,
        },
    )
    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        f"&state={state}"
        f"&scope={CURRENT_SCOPE.replace(' ', '+')}"
    )

    client = await client_factory()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "updated-refresh-token",
            "access_token": token,
            "type": "Bearer",
            "expires_in": "60",
            "scope": CURRENT_SCOPE,
        },
    )

    with patch(
        f"homeassistant.components.{DOMAIN}.async_setup_entry", return_value=True
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        await hass.async_block_till_done()

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal(expected_reason)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
