"""Test the SENZ config flow."""

from unittest.mock import patch

from pysenz import AUTHORIZATION_ENDPOINT, TOKEN_ENDPOINT
from tryke import Depends, expect, fixture, test

from homeassistant import config_entries
from homeassistant.components.senz.const import DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import access_token, expires_at, mock_config_entry, setup_credentials
from .const import CLIENT_ID, ENTRY_UNIQUE_ID

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    aioclient_mock as aioclient_mock_fixture,
    current_request_with_host,
    hass as hass_fixture,
    hass_client_no_auth as hass_client_no_auth_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker
from tests.typing import ClientSessionGenerator

REDIRECT_PATH = "/auth/external/callback"
REDIRECT_URL = "https://example.com" + REDIRECT_PATH


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _request: None = Depends(current_request_with_host),
    _credentials: None = Depends(setup_credentials),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    access_token: str = Depends(access_token),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        "senz", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URL,
        },
    )

    expect(result["url"]).to_equal(
        f"{AUTHORIZATION_ENDPOINT}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        f"&state={state}&scope=restapi+offline_access+openid"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"{REDIRECT_PATH}?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        TOKEN_ENDPOINT,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": access_token,
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.senz.async_setup_entry", return_value=True
    ) as mock_setup:
        await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)


@test
async def duplicate_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    access_token: str = Depends(access_token),
) -> None:
    """Check full flow with duplicate entry."""
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
        f"{AUTHORIZATION_ENDPOINT}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        f"&state={state}&scope=restapi+offline_access+openid"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"{REDIRECT_PATH}?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        TOKEN_ENDPOINT,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": access_token,
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch("homeassistant.components.senz.async_setup_entry", return_value=True):
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result2["type"]).to_be(FlowResultType.ABORT)
    expect(result2["reason"]).to_equal("already_configured")


@test
async def reauth_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    access_token: str = Depends(access_token),
    expires_at_value: float = Depends(expires_at),
) -> None:
    """Test reauth step with correct params."""
    CURRENT_TOKEN = {
        "auth_implementation": DOMAIN,
        "token": {
            "access_token": access_token,
            "expires_in": 86399,
            "refresh_token": "3012bc9f-7a65-4240-b817-9154ffdcc30f",
            "token_type": "Bearer",
            "expires_at": expires_at_value,
        },
    }
    expect(
        hass.config_entries.async_update_entry(
            config_entry,
            data=CURRENT_TOKEN,
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
        f"{AUTHORIZATION_ENDPOINT}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        f"&state={state}&scope=restapi+offline_access+openid"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"{REDIRECT_PATH}?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        TOKEN_ENDPOINT,
        json={
            "refresh_token": "updated-refresh-token",
            "access_token": access_token,
            "type": "Bearer",
            "expires_in": "60",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test.cases(
    test.case(
        "matching",
        unique_id_value=ENTRY_UNIQUE_ID,
        expected_result="reconfigure_successful",
    ),
    test.case(
        "different",
        unique_id_value="different_unique_id",
        expected_result="account_mismatch",
    ),
)
async def reconfiguration_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    access_token: str = Depends(access_token),
    expires_at_value: float = Depends(expires_at),
    *,
    unique_id_value: str,
    expected_result: str,
) -> None:
    """Test reconfigure step with correct params."""
    CURRENT_TOKEN = {
        "auth_implementation": DOMAIN,
        "token": {
            "access_token": access_token,
            "expires_in": 86399,
            "refresh_token": "3012bc9f-7a65-4240-b817-9154ffdcc30f",
            "token_type": "Bearer",
            "expires_at": expires_at_value,
        },
    }
    expect(
        hass.config_entries.async_update_entry(
            config_entry,
            data=CURRENT_TOKEN,
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
        f"{AUTHORIZATION_ENDPOINT}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        f"&state={state}&scope=restapi+offline_access+openid"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"{REDIRECT_PATH}?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        TOKEN_ENDPOINT,
        json={
            "refresh_token": "updated-refresh-token",
            "access_token": access_token,
            "type": "Bearer",
            "expires_in": "60",
        },
    )

    # Mutate unique_id for the "different" case to drive account_mismatch
    if unique_id_value != ENTRY_UNIQUE_ID:
        hass.config_entries.async_update_entry(config_entry, unique_id=unique_id_value)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal(expected_result)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
