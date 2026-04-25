"""Test the Miele config flow."""

from unittest.mock import AsyncMock

from pymiele import OAUTH2_AUTHORIZE, OAUTH2_TOKEN
from tryke import Depends, expect, fixture, test

from homeassistant.components.miele.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER, SOURCE_ZEROCONF
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    access_token,
    expires_at,
    mock_config_entry,
    mock_setup_entry,
    setup_credentials,
)
from .const import CLIENT_ID

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

REDIRECT_URL = "https://example.com/auth/external/callback"


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
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
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
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result.get("type")).to_be(FlowResultType.EXTERNAL_STEP)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def flow_reauth_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    token: str = Depends(access_token),
    expires: float = Depends(expires_at),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reauth step with correct params."""
    CURRENT_TOKEN = {
        "auth_implementation": DOMAIN,
        "token": {
            "access_token": token,
            "expires_in": 86399,
            "refresh_token": "3012bc9f-7a65-4240-b817-9154ffdcc30f",
            "token_type": "Bearer",
            "expires_at": expires,
        },
    }
    expect(
        bool(
            hass.config_entries.async_update_entry(
                config_entry,
                data=CURRENT_TOKEN,
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
    )

    client = await client_gen()
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
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def flow_reconfigure_abort(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
    token: str = Depends(access_token),
    expires: float = Depends(expires_at),
    _setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test reconfigure step with correct params."""
    CURRENT_TOKEN = {
        "auth_implementation": DOMAIN,
        "token": {
            "access_token": token,
            "expires_in": 86399,
            "refresh_token": "3012bc9f-7a65-4240-b817-9154ffdcc30f",
            "token_type": "Bearer",
            "expires_at": expires,
        },
    }
    expect(
        bool(
            hass.config_entries.async_update_entry(
                config_entry,
                data=CURRENT_TOKEN,
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
    )

    client = await client_gen()
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
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reconfigure_successful")

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def zeroconf_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
) -> None:
    """Test zeroconf flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}
    )

    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("oauth_discovery")
    expect(bool(result["errors"])).to_be(False)

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {},
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
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    expect(result.get("type")).to_be(FlowResultType.EXTERNAL_STEP)

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)
    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)

    config_entry = result["result"]
    expect(config_entry.domain).to_equal("miele")
