"""Tests for the Spotify config flow."""

from http import HTTPStatus
from unittest.mock import MagicMock, patch

from spotifyaio import SpotifyConnectionError, SpotifyForbiddenError
from tryke import Depends, expect, fixture, test

from homeassistant.components.spotify.const import DOMAIN
from homeassistant.config_entries import SOURCE_USER
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.helpers import config_entry_oauth2_flow

from ._fixtures import (
    mock_config_entry,
    mock_spotify,
    patch_sleep,
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
    _sleep: None = Depends(patch_sleep),
) -> None:
    """Apply autouse-equivalent fixtures via this trigger."""


@test
async def abort_if_no_configuration(
    _trigger: None = Depends(_trigger_executor),
    hass: HomeAssistant = Depends(hass_fixture),
) -> None:
    """Check flow aborts when no configuration is present."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("missing_credentials")


@test
async def full_flow(
    _trigger: None = Depends(_trigger_executor),
    _request: None = Depends(current_request_with_host),
    _credentials: None = Depends(setup_credentials),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _spotify: MagicMock = Depends(mock_spotify),
) -> None:
    """Check a full flow."""
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
        "https://accounts.spotify.com/authorize"
        "?response_type=code&client_id=CLIENT_ID"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        "&scope=user-modify-playback-state,user-read-playback-state,user-read-private,"
        "playlist-read-private,playlist-read-collaborative,user-library-read,"
        "user-top-read,user-read-playback-position,user-read-recently-played,user-follow-read"
    )

    client = await client_gen()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    expect(resp.status).to_equal(HTTPStatus.OK)
    expect(resp.headers["content-type"]).to_equal("text/html; charset=utf-8")

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        "https://accounts.spotify.com/api/token",
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch("homeassistant.components.spotify.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.CREATE_ENTRY)
    expect(len(hass.config_entries.async_entries(DOMAIN))).to_equal(1)

    result["data"]["token"].pop("expires_at")
    expect(result["data"]["name"]).to_equal("Henk")
    expect(result["data"]["token"]).to_equal(
        {
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        }
    )
    expect(result["result"].unique_id).to_equal("1112264111")


@test.cases(
    test.case(
        "connection_error",
        exception=SpotifyConnectionError,
        reason="connection_error",
    ),
    test.case(
        "user_not_premium",
        exception=SpotifyForbiddenError,
        reason="user_not_premium",
    ),
)
async def abort_if_spotify_error(
    _trigger: None = Depends(_trigger_executor),
    _request: None = Depends(current_request_with_host),
    _credentials: None = Depends(setup_credentials),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    spotify: MagicMock = Depends(mock_spotify),
    *,
    exception: type[Exception],
    reason: str,
) -> None:
    """Check Spotify errors causes flow to abort."""
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
    client = await client_gen()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")

    aioclient_mock.post(
        "https://accounts.spotify.com/api/token",
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    spotify.return_value.get_current_user.side_effect = exception

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal(reason)


@test
async def reauthentication(
    _trigger: None = Depends(_trigger_executor),
    _request: None = Depends(current_request_with_host),
    _credentials: None = Depends(setup_credentials),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    _spotify: MagicMock = Depends(mock_spotify),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test Spotify reauthentication."""
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
    client = await client_gen()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")

    aioclient_mock.post(
        "https://accounts.spotify.com/api/token",
        json={
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch("homeassistant.components.spotify.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_successful")
    config_entry.data["token"].pop("expires_at")
    expect(config_entry.data["token"]).to_equal(
        {
            "refresh_token": "new-refresh-token",
            "access_token": "new-access-token",
            "type": "Bearer",
            "expires_in": 60,
        }
    )


@test
async def reauth_account_mismatch(
    _trigger: None = Depends(_trigger_executor),
    _request: None = Depends(current_request_with_host),
    _credentials: None = Depends(setup_credentials),
    hass: HomeAssistant = Depends(hass_fixture),
    client_gen: ClientSessionGenerator = Depends(hass_client_no_auth),
    aioclient_mock: AiohttpClientMocker = Depends(aioclient_mock_fx),
    spotify: MagicMock = Depends(mock_spotify),
    config_entry: MockConfigEntry = Depends(mock_config_entry),
) -> None:
    """Test Spotify reauthentication with different account."""
    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await client_gen()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")

    aioclient_mock.post(
        "https://accounts.spotify.com/api/token",
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    spotify.return_value.get_current_user.return_value.user_id = "different_user_id"
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    expect(result["type"]).to_be(FlowResultType.ABORT)
    expect(result["reason"]).to_equal("reauth_account_mismatch")
