"""Test the Electric Kiwi config flow."""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import AsyncMock

from electrickiwi_api.exceptions import ApiException
from tryke import Depends, expect, fixture, test

from homeassistant.components.electric_kiwi.const import (
    DOMAIN,
    OAUTH2_AUTHORIZE,
    OAUTH2_TOKEN,
    SCOPE_VALUES,
)
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    CLIENT_ID,
    REDIRECT_URI,
    electrickiwi_api,
    migrated_config_entry,
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
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    _api: AsyncMock = Depends(electrickiwi_api),
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

    url_scope = SCOPE_VALUES.replace(" ", "+")

    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
        f"&scope={url_scope}"
    )

    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
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

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)


@test
async def flow_failure(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    api: AsyncMock = Depends(electrickiwi_api),
) -> None:
    """Check failure on creation of entry."""
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

    url_scope = SCOPE_VALUES.replace(" ", "+")

    expect(result["url"]).to_equal(
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&state={state}"
        f"&scope={url_scope}"
    )

    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    api.get_active_session.side_effect = ApiException()

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(0)
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("connection_error")


@test
async def existing_entry(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(migrated_config_entry),
    _api: AsyncMock = Depends(electrickiwi_api),
) -> None:
    """Check existing entry."""
    config_entry.add_to_hass(hass)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER, "entry_id": DOMAIN}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": OAUTH2_AUTHORIZE,
        },
    )

    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "expires_in": 3599,
            "refresh_token": "mock-refresh_token",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("already_configured")
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)


@test
async def reauthentication(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    setup_entry: AsyncMock = Depends(mock_setup_entry),
    config_entry: MockConfigEntry = Depends(migrated_config_entry),
    _api: AsyncMock = Depends(electrickiwi_api),
) -> None:
    """Test Electric Kiwi reauthentication."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    expect(result["type"]).to_be(FlowResultType.FORM)
    expect(result["step_id"]).to_equal("reauth_confirm")

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URI,
        },
    )

    http_client = await client()
    resp = await http_client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.post(
        OAUTH2_TOKEN,
        json={
            "access_token": "mock-access-token",
            "token_type": "bearer",
            "expires_in": 3599,
            "refresh_token": "mock-refresh_token",
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    await hass.async_block_till_done()

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(setup_entry.mock_calls)).to_equal(1)

    expect(result.get("type")).to_be(FlowResultType.ABORT)
    expect(result.get("reason")).to_equal("reauth_successful")
