"""Tests for config flow."""

from unittest.mock import AsyncMock, patch

from tryke import Depends, expect, fixture, test

from homeassistant.components.withings.const import DOMAIN
from homeassistant.config_entries import SOURCE_DHCP, SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow
from homeassistant.helpers.service_info.dhcp import DhcpServiceInfo

from . import setup_integration
from ._fixtures import (
    CLIENT_ID,
    USER_ID,
    disable_webhook_delay,
    polling_config_entry,
    setup_credentials,
    withings as withings_fx,
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
    _request: None = Depends(current_request_with_host),
    _credentials: None = Depends(setup_credentials),
    _delay: None = Depends(disable_webhook_delay),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
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
        "https://account.withings.com/oauth2_user/authorize2?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        "&scope=user.info,user.metrics,user.activity,user.sleepevents"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "https://wbsapi.withings.net/v2/oauth2",
        json={
            "body": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
                "userid": 600,
            },
        },
    )
    with patch(
        "homeassistant.components.withings.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(result["title"]).to_equal("Withings")
    expect("result" in result).to_be(True)
    expect(result["result"].unique_id).to_equal("600")
    expect("token" in result["result"].data).to_be(True)
    expect("webhook_id" in result["result"].data).to_be(True)
    expect(result["result"].data["token"]["access_token"]).to_equal("mock-access-token")
    expect(result["result"].data["token"]["refresh_token"]).to_equal(
        "mock-refresh-token"
    )


@test
async def config_non_unique_profile(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    _withings: AsyncMock = Depends(withings_fx),
    config_entry: MockConfigEntry = Depends(polling_config_entry),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
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
        "https://account.withings.com/oauth2_user/authorize2?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        "&scope=user.info,user.metrics,user.activity,user.sleepevents"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "https://wbsapi.withings.net/v2/oauth2",
        json={
            "body": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
                "userid": USER_ID,
            },
        },
    )
    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("already_configured")


@test
async def config_reauth_profile(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(polling_config_entry),
    _withings: AsyncMock = Depends(withings_fx),
) -> None:
    """Test reauth an existing profile reauthenticates the config entry."""
    await setup_integration(hass, config_entry)

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
    expect(result["url"]).to_equal(
        "https://account.withings.com/oauth2_user/authorize2?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        "&scope=user.info,user.metrics,user.activity,user.sleepevents"
    )
    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "https://wbsapi.withings.net/v2/oauth2",
        json={
            "body": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
                "userid": USER_ID,
            },
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")


@test
async def config_reauth_wrong_account(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    config_entry: MockConfigEntry = Depends(polling_config_entry),
    _withings: AsyncMock = Depends(withings_fx),
) -> None:
    """Test reauth with wrong account."""
    await setup_integration(hass, config_entry)

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
    expect(result["url"]).to_equal(
        "https://account.withings.com/oauth2_user/authorize2?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        "&scope=user.info,user.metrics,user.activity,user.sleepevents"
    )
    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "https://wbsapi.withings.net/v2/oauth2",
        json={
            "body": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
                "userid": 12346,
            },
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("wrong_account")


@test
async def config_flow_with_invalid_credentials(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _config_entry: MockConfigEntry = Depends(polling_config_entry),
    _withings: AsyncMock = Depends(withings_fx),
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
        "https://account.withings.com/oauth2_user/authorize2?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        "&scope=user.info,user.metrics,user.activity,user.sleepevents"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "https://wbsapi.withings.net/v2/oauth2",
        json={
            "body": {
                "status": 503,
                "error": "Invalid Params: invalid client id/secret",
            },
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("oauth_error")


@test
async def dhcp(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
) -> None:
    """Check DHCP discovery."""
    service_info = DhcpServiceInfo(
        hostname="device",
        ip="192.168.0.1",
        macaddress="0024e4bd30de",
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=service_info
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
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    expect(result["type"]).to_be(FlowResultType.EXTERNAL_STEP)
    expect(result["url"]).to_equal(
        "https://account.withings.com/oauth2_user/authorize2?"
        f"response_type=code&client_id={CLIENT_ID}&"
        "redirect_uri=https://example.com/auth/external/callback&"
        f"state={state}"
        "&scope=user.info,user.metrics,user.activity,user.sleepevents"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(200)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "https://wbsapi.withings.net/v2/oauth2",
        json={
            "body": {
                "refresh_token": "mock-refresh-token",
                "access_token": "mock-access-token",
                "type": "Bearer",
                "expires_in": 60,
                "userid": 600,
            },
        },
    )
    with patch(
        "homeassistant.components.withings.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)
    expect(len(mock_setup.mock_calls)).to_equal(1)

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
