"""Test the Geocaching config flow."""

from http import HTTPStatus
from unittest.mock import MagicMock

from tryke import Depends, expect, fixture, test

from homeassistant.components.geocaching.const import (
    DOMAIN,
    ENVIRONMENT,
    ENVIRONMENT_URLS,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    mock_config_entry,
    mock_geocaching_config_flow,
    mock_setup_entry,
    setup_credentials,
)

from . import CLIENT_ID, REDIRECT_URI

from tests.common import MockConfigEntry
from tests.hass_fixtures import (
    ClientSessionGenerator,
    aioclient_mock as aioclient_mock_fixture,
    aiohttp_client as aiohttp_client_fixture,
    current_request_with_host as current_request_with_host_fixture,
    hass as hass_fixture,
    hass_client_no_auth as hass_client_no_auth_fixture,
    mock_network,
)
from tests.test_util.aiohttp import AiohttpClientMocker

CURRENT_ENVIRONMENT_URLS = ENVIRONMENT_URLS[ENVIRONMENT]


@fixture
def _trigger_executor(
    _network: None = Depends(mock_network),
    _request_with_host: None = Depends(current_request_with_host_fixture),
) -> None:
    """Present so tryke builds a fixture executor for this module."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _credentials: None = Depends(setup_credentials),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    _flow: MagicMock = Depends(mock_geocaching_config_flow),
    setup_entry: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URI,
        },
    )

    expect(result.get("type")).to_be(FlowResultType.EXTERNAL_STEP)
    expect(result.get("step_id")).to_equal("auth")
    expect(result.get("url")).to_equal(
        f"{CURRENT_ENVIRONMENT_URLS['authorize_url']}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}&scope=*"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        CURRENT_ENVIRONMENT_URLS["token_url"],
        json={
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "expires_in": 3599,
            "refresh_token": "mock-refresh_token",
        },
    )

    await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _credentials: None = Depends(setup_credentials),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    _flow: MagicMock = Depends(mock_geocaching_config_flow),
    _setup: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Check existing entry."""
    config_entry.add_to_hass(hass)

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URI,
        },
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        CURRENT_ENVIRONMENT_URLS["token_url"],
        json={
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "expires_in": 3599,
            "refresh_token": "mock-refresh_token",
        },
    )

    await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def oauth_error(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _credentials: None = Depends(setup_credentials),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    flow: MagicMock = Depends(mock_geocaching_config_flow),
    setup_entry: MagicMock = Depends(mock_setup_entry),
) -> None:
    """Check if aborted when oauth error occurs."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URI,
        },
    )
    expect(result.get("type")).to_be(FlowResultType.EXTERNAL_STEP)

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)

    flow.update.return_value.user = None

    aioclient_mock.post(
        CURRENT_ENVIRONMENT_URLS["token_url"],
        json={
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "expires_in": 3599,
            "refresh_token": "mock-refresh_token",
        },
    )

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result2.get("type")).to_be(FlowResultType.ABORT)
    expect(result2.get("reason")).to_equal("oauth_error")

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(0)
    expect(len(setup_entry.mock_calls)).to_equal(0)


@test
async def reauthentication(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    _credentials: None = Depends(setup_credentials),
    hass_client_no_auth: ClientSessionGenerator = Depends(hass_client_no_auth_fixture),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fixture),
    _flow: MagicMock = Depends(mock_geocaching_config_flow),
    setup_entry: MagicMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test Geocaching reauthentication."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    flows = hass.config_entries.flow.async_progress()
    expect(len(flows)).to_equal(1)
    expect("flow_id" in flows[0]).to_be(True)

    result = await hass.config_entries.flow.async_configure(flows[0]["flow_id"], {})

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        CURRENT_ENVIRONMENT_URLS["token_url"],
        json={
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "expires_in": 3599,
            "refresh_token": "mock-refresh_token",
        },
    )

    await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)
